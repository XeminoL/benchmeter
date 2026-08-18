import argparse
import json
import sys

from . import chandoan, ketluan, lichsu, onhdinh
from .dothinghiem import NGAN_SACH_GIAY_MAC_DINH, do_xen_ke
from .dongho import kiem_lenh_chay_duoc


def _tao_bo_phan_tich():
    bo = argparse.ArgumentParser(
        prog="doluong",
        description="Do hieu nang va biet khi nao khong du tin de ket luan.",
    )
    bo.add_argument("lenh", nargs="*",
                    help="cac lenh can so sanh, dat trong dau nhay")
    bo.add_argument("-n", "--so-lan", type=int, default=None,
                    help="so vong do (mac dinh: tu tinh theo ngan sach)")
    bo.add_argument("-t", "--ngan-sach", type=float,
                    default=NGAN_SACH_GIAY_MAC_DINH,
                    help="ngan sach thoi gian tinh bang giay")
    bo.add_argument("--nhan", action="append", default=None,
                    help="ten hien thi cho tung lenh")
    bo.add_argument("--hat-giong", type=int, default=None,
                    help="hat giong ngau nhien de lap lai y het")
    bo.add_argument("--khong-xao", action="store_true",
                    help="khong xao thu tu trong moi vong")
    bo.add_argument("--json", action="store_true",
                    help="xuat ket qua dang json")
    bo.add_argument("--luu", action="store_true",
                    help="luu ket qua vao lich su de so lan sau")
    bo.add_argument("--ghi-chu", default="",
                    help="ghi chu kem theo khi luu")
    bo.add_argument("--kiem-may", action="store_true",
                    help="chi kiem tinh trang may roi thoat")
    bo.add_argument("--tu-chung-minh", action="store_true",
                    help="chay thi nghiem chung minh van de la that")
    bo.add_argument("--bo-qua-kiem-may", action="store_true",
                    help="khong kiem may truoc khi do")
    bo.add_argument("--on-dinh", action="store_true",
                    help="ghim nhan CPU + nang uu tien + tat don rac")
    return bo


def _in_tinh_trang_may(tinh_trang):
    print()
    print("TINH TRANG MAY")
    print("-" * 56)
    print(f"  xep loai        : {tinh_trang.xep_loai}")
    print(f"  do troi         : {tinh_trang.do_troi * 100:.1f}%")
    print(f"  bien thien      : {tinh_trang.he_so_bien_thien * 100:.1f}%")
    print(f"  phan biet duoc  : tu {tinh_trang.phan_giai * 100:.1f}% tro len")
    print(f"  tu tuong quan   : {tinh_trang.tu_tuong_quan:+.3f}")
    print()
    print(f"  {tinh_trang.loi_khuyen()}")
    print()


def _xuat_json(bao_cao):
    du_lieu = {
        "so_vong": bao_cao.ket_qua.so_vong,
        "dung_som": bao_cao.ket_qua.dung_som,
        "may": {
            "xep_loai": bao_cao.tinh_trang_may.xep_loai,
            "do_troi": bao_cao.tinh_trang_may.do_troi,
            "phan_giai": bao_cao.tinh_trang_may.phan_giai,
        },
        "ket_qua": [
            {
                "nhan": m.nhan,
                "so_mau": len(m),
                "so_lan_loi": m.so_lan_loi,
                "thoi_gian_ns": m.thoi_gian,
            }
            for m in bao_cao.ket_qua.mau
        ],
        "so_sanh": [
            {
                "goc": s.goc.nhan,
                "khac": s.khac.nhan,
                "ty_le": s.ty_le,
                "can_duoi": s.can_duoi,
                "can_tren": s.can_tren,
                "ket_luan_duoc": s.ket_luan_duoc,
            }
            for s in bao_cao.cac_so_sanh
        ],
    }
    print(json.dumps(du_lieu, indent=2, ensure_ascii=False))


def chay(doi_so=None):
    bo = _tao_bo_phan_tich()
    tham_so = bo.parse_args(doi_so)

    if tham_so.on_dinh:
        ket_qua_on_dinh = onhdinh.on_dinh_may()
        if not tham_so.json:
            print(f"\n  on dinh may: {ket_qua_on_dinh.mo_ta()}")
            for loi in ket_qua_on_dinh.loi:
                print(f"    khong lam duoc: {loi}")

    if tham_so.kiem_may:
        _in_tinh_trang_may(chandoan.do_may())
        if tham_so.on_dinh:
            onhdinh.tra_lai_binh_thuong()
        return 0

    if tham_so.tu_chung_minh:
        from . import tuchungminh
        tuchungminh.chay()
        if tham_so.on_dinh:
            onhdinh.tra_lai_binh_thuong()
        return 0

    if not tham_so.lenh:
        bo.print_help()
        return 1

    for lenh in tham_so.lenh:
        chay_duoc, _ = kiem_lenh_chay_duoc(lenh)
        if not chay_duoc:
            print(f"loi: lenh khong chay duoc: {lenh}", file=sys.stderr)
            return 1

    nhan = tham_so.nhan
    if nhan and len(nhan) != len(tham_so.lenh):
        print("loi: so nhan khong khop so lenh", file=sys.stderr)
        return 1

    tinh_trang = None
    if not tham_so.bo_qua_kiem_may:
        tinh_trang = chandoan.kiem_truoc_khi_do()
        if not tham_so.json:
            _in_tinh_trang_may(tinh_trang)
    else:
        tinh_trang = chandoan.TinhTrangMay(0.0, 0.0, 0.0, 0.0, da_kiem=False)

    hien_tien_do = not tham_so.json and sys.stderr.isatty()

    def tien_do(vong, tong):
        if hien_tien_do:
            print(f"\r  dang do... vong {vong}/{tong}",
                  end="", file=sys.stderr, flush=True)

    ket_qua = do_xen_ke(
        tham_so.lenh, nhan,
        so_lan=tham_so.so_lan,
        ngan_sach_giay=tham_so.ngan_sach,
        hat_giong=tham_so.hat_giong,
        xao_thu_tu=not tham_so.khong_xao,
        bao_tien_do=tien_do,
        phan_giai_may=tinh_trang.phan_giai,
    )
    if hien_tien_do:
        print("\r" + " " * 40 + "\r", end="", file=sys.stderr)

    bao_cao = ketluan.phan_tich(ket_qua, tinh_trang,
                                hat_giong=tham_so.hat_giong)

    if tham_so.json:
        _xuat_json(bao_cao)
    else:
        print(ketluan.in_bao_cao(bao_cao))
        so_sanh = lichsu.so_voi_lan_truoc(bao_cao)
        if so_sanh:
            print(lichsu.in_so_sanh(so_sanh))

    if tham_so.luu:
        lichsu.ghi(bao_cao, tham_so.ghi_chu)

    if tham_so.on_dinh:
        onhdinh.tra_lai_binh_thuong()

    return 0 if bao_cao.co_ket_luan else 2


if __name__ == "__main__":
    sys.exit(chay())

"""Tu chay lai thi nghiem chung minh cong cu nay dang giai quyet van de that.

Khong tin loi ai ke, ke ca loi cua chinh cong cu nay. Chay lenh nay
tren may cua ban de tu thay:
  1. May co troi trong luc do khong
  2. Cong thuc chia can N bao sai bao nhieu lan
  3. Do xen ke giam duoc bao nhieu
"""
import statistics
import time

from . import thongke
from .dongho import doc_duoc

SO_LAN_DO = 6000
KICH_THUOC_KHOI = 300
KICH_THUOC_DOAN = 40
SO_CAP_KIEM = 150
Z_95 = 1.959964


def _tac_vu():
    tong = 0
    for i in range(3000):
        tong += i * i
    return tong


def _do_lien_tuc(so_lan):
    mau = []
    for _ in range(so_lan):
        bat_dau = time.perf_counter_ns()
        _tac_vu()
        mau.append(time.perf_counter_ns() - bat_dau)
    return mau


def _cach_cu_bao_khac(a, b):
    """Cong thuc chia can N - cach hyperfine va sach vat ly dai cuong dung."""
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    sa = statistics.stdev(a) / len(a) ** 0.5
    sb = statistics.stdev(b) / len(b) ** 0.5
    return abs(ma - mb) > Z_95 * (sa + sb)


def _dem_bao_sai_tuan_tu(mau):
    """Do het A roi moi do B - hai doan lien tiep trong thoi gian."""
    sai = tong = 0
    buoc = KICH_THUOC_DOAN * 2
    for i in range(0, len(mau) - buoc, buoc):
        a = mau[i:i + KICH_THUOC_DOAN]
        b = mau[i + KICH_THUOC_DOAN:i + buoc]
        tong += 1
        if _cach_cu_bao_khac(a, b):
            sai += 1
        if tong >= SO_CAP_KIEM:
            break
    return sai, tong


def _dem_bao_sai_xen_ke(mau):
    """Do xen ke - lay xen ke tu cung mot doan."""
    sai = tong = 0
    buoc = KICH_THUOC_DOAN * 2
    for i in range(0, len(mau) - buoc, buoc):
        cua_so = mau[i:i + buoc]
        a = cua_so[0::2]
        b = cua_so[1::2]
        tong += 1
        _, duoi, tren = thongke.khoang_tin_cay_hieu(a, b, so_lan=400,
                                                    hat_giong=i)
        if thongke.du_tin_de_ket_luan(duoi, tren):
            sai += 1
        if tong >= SO_CAP_KIEM:
            break
    return sai, tong


def chay(bao=print):
    bao("")
    bao("TU CHUNG MINH")
    bao("=" * 58)
    bao("Do cung MOT tac vu nhieu lan. Moi ket luan 'hai ben khac nhau'")
    bao("deu la ket luan SAI, vi chung von la mot.")
    bao("")

    bao(f"Dang do {SO_LAN_DO:,} lan...")
    mau = _do_lien_tuc(SO_LAN_DO)

    bao("")
    bao("1. MAY CO TROI TRONG LUC DO KHONG")
    bao("-" * 58)
    khoi = []
    for i in range(0, len(mau), KICH_THUOC_KHOI):
        doan = mau[i:i + KICH_THUOC_KHOI]
        if len(doan) >= KICH_THUOC_KHOI // 2:
            khoi.append(statistics.median(doan))
    thap, cao = min(khoi), max(khoi)
    bao(f"   khoi nhanh nhat : {doc_duoc(thap)}")
    bao(f"   khoi cham nhat  : {doc_duoc(cao)}")
    bao(f"   chenh lech      : {(cao - thap) / thap * 100:.1f}%")
    bao("")
    bao("   -> Cung mot tac vu, khong doi gi, ma luc nhanh luc cham.")
    bao("      Nghia la khong ton tai 'mot gia tri that' co dinh.")

    bao("")
    bao("2. CACH DO CU BAO SAI BAO NHIEU")
    bao("-" * 58)
    sai_cu, tong_cu = _dem_bao_sai_tuan_tu(mau)
    bao(f"   do tuan tu, dung cong thuc chia can N:")
    bao(f"   bao 'khac nhau co y nghia' {sai_cu}/{tong_cu} lan "
        f"= {sai_cu / tong_cu * 100:.1f}%")
    bao("   -> Tat ca deu SAI, vi hai ben von la cung mot tac vu.")

    bao("")
    bao("3. CACH DO XEN KE")
    bao("-" * 58)
    sai_moi, tong_moi = _dem_bao_sai_xen_ke(mau)
    bao(f"   bao 'khac nhau co y nghia' {sai_moi}/{tong_moi} lan "
        f"= {sai_moi / tong_moi * 100:.1f}%")

    bao("")
    bao("=" * 58)
    if sai_cu > 0:
        giam = (1 - (sai_moi / tong_moi) / (sai_cu / tong_cu)) * 100
        bao(f"   Xen ke giam bao sai {giam:.0f}%")
    bao(f"   ({sai_cu / tong_cu * 100:.1f}% -> {sai_moi / tong_moi * 100:.1f}%)")
    bao("")
    bao("   Chay lai lenh nay bat cu luc nao de tu kiem.")
    bao("")

    return {
        "do_troi": (cao - thap) / thap,
        "bao_sai_tuan_tu": sai_cu / tong_cu,
        "bao_sai_xen_ke": sai_moi / tong_moi,
    }

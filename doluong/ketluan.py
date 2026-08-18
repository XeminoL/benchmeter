from . import thongke
from .dongho import doc_duoc

NGUONG_KHAC_BIET_NHO = 0.02


class SoSanh:
    def __init__(self, goc, khac, ty_le, can_duoi, can_tren, ket_luan_duoc):
        self.goc = goc
        self.khac = khac
        self.ty_le = ty_le
        self.can_duoi = can_duoi
        self.can_tren = can_tren
        self.ket_luan_duoc = ket_luan_duoc

    @property
    def phan_tram(self):
        return (self.ty_le - 1) * 100

    @property
    def nhanh_hon(self):
        return self.ty_le < 1

    @property
    def bien_do_phan_tram(self):
        return ((self.can_tren - self.can_duoi) / 2) * 100


class BaoCao:
    def __init__(self, ket_qua, tinh_trang_may, cac_so_sanh):
        self.ket_qua = ket_qua
        self.tinh_trang_may = tinh_trang_may
        self.cac_so_sanh = cac_so_sanh

    @property
    def co_ket_luan(self):
        return all(s.ket_luan_duoc for s in self.cac_so_sanh)


def phan_tich(ket_qua, tinh_trang_may, hat_giong=None):
    mau = ket_qua.mau
    goc = mau[0]
    so_sanh = []
    for khac in mau[1:]:
        n = min(len(goc), len(khac))
        ty_le, duoi, tren = thongke.khoang_tin_cay_hieu(
            goc.thoi_gian[:n], khac.thoi_gian[:n], hat_giong=hat_giong)
        so_sanh.append(SoSanh(
            goc=goc, khac=khac, ty_le=ty_le,
            can_duoi=duoi, can_tren=tren,
            ket_luan_duoc=thongke.du_tin_de_ket_luan(duoi, tren),
        ))
    return BaoCao(ket_qua, tinh_trang_may, so_sanh)


def _dong_ket_qua(mau):
    tv = thongke.trung_vi(mau.thoi_gian)
    bien = thongke.he_so_bien_thien(mau.thoi_gian) * 100
    return f"{mau.nhan:<28} {doc_duoc(tv):>12}   +-{bien:>5.1f}%"


def _giai_thich_khong_ket_luan(so_sanh, tinh_trang_may, ket_qua):
    lech = abs(so_sanh.phan_tram)
    troi = tinh_trang_may.do_troi * 100
    phan_giai = tinh_trang_may.phan_giai * 100
    dong = []
    dong.append(f"  CHUA KET LUAN DUOC")
    dong.append(f"  Do duoc chenh lech {lech:.1f}%, nhung khoang tin cay "
                f"tu {(so_sanh.can_duoi - 1) * 100:+.1f}% "
                f"den {(so_sanh.can_tren - 1) * 100:+.1f}%")
    dong.append(f"  -> khoang nay bao gom ca 0, tuc chua loai tru duoc "
                f"kha nang hai lenh nhanh nhu nhau.")
    dong.append("")
    dong.append("  Lam gi tiep:")
    if tinh_trang_may.dang_ban:
        dong.append(f"    - May dang troi {troi:.0f}%. Dong bot ung dung "
                    f"roi do lai.")
    if lech < phan_giai:
        dong.append(f"    - May nay chi phan biet duoc chenh lech tu "
                    f"{phan_giai:.1f}% tro len.")
        dong.append(f"      Chenh lech {lech:.1f}% nam duoi nguong do.")
    can_them = _uoc_so_lan_can_them(so_sanh, ket_qua)
    if can_them:
        dong.append(f"    - Do them khoang {can_them} vong nua co the du.")
    if lech < 1:
        dong.append("    - Hai lenh nay gan nhu chac chan nhanh nhu nhau.")
    return dong


def _uoc_so_lan_can_them(so_sanh, ket_qua):
    """Bien do thu hep theo can bac hai so mau."""
    lech = abs(so_sanh.phan_tram)
    bien = so_sanh.bien_do_phan_tram
    if lech <= 0 or bien <= lech:
        return 0
    he_so = (bien / lech) ** 2
    can = int(ket_qua.so_vong * (he_so - 1))
    if can <= 0 or can > 5000:
        return 0
    return can


def in_bao_cao(bao_cao):
    ket_qua = bao_cao.ket_qua
    may = bao_cao.tinh_trang_may
    dong = []

    dong.append("")
    dong.append("KET QUA DO")
    dong.append("-" * 56)
    for mau in ket_qua.mau:
        dong.append("  " + _dong_ket_qua(mau))
    dong.append("")
    dong.append(f"  do xen ke {ket_qua.so_vong} vong"
                + (" (dung som vi da du ro)" if ket_qua.dung_som else ""))
    if may.da_kiem:
        dong.append(f"  tinh trang may: {may.xep_loai} "
                    f"(troi {may.do_troi * 100:.0f}%, "
                    f"phan biet duoc tu {may.phan_giai * 100:.1f}%)")
    else:
        dong.append("  tinh trang may: chua kiem")

    for so_sanh in bao_cao.cac_so_sanh:
        dong.append("")
        dong.append("-" * 56)
        if so_sanh.ket_luan_duoc:
            huong = "nhanh hon" if so_sanh.nhanh_hon else "cham hon"
            dong.append(f"  {so_sanh.khac.nhan} {huong} "
                        f"{abs(so_sanh.phan_tram):.1f}% so voi "
                        f"{so_sanh.goc.nhan}")
            dong.append(f"  khoang tin cay 95%: "
                        f"{(so_sanh.can_duoi - 1) * 100:+.1f}% den "
                        f"{(so_sanh.can_tren - 1) * 100:+.1f}%")
            muc = thongke.muc_do_tin(may.do_troi, len(so_sanh.goc),
                                     may.he_so_bien_thien)
            dong.append(f"  do tin: {muc}")
        else:
            dong.extend(_giai_thich_khong_ket_luan(so_sanh, may, ket_qua))

    if any(m.so_lan_loi for m in ket_qua.mau):
        dong.append("")
        for m in ket_qua.mau:
            if m.so_lan_loi:
                dong.append(f"  canh bao: {m.nhan} loi {m.so_lan_loi} lan")

    dong.append("")
    return "\n".join(dong)

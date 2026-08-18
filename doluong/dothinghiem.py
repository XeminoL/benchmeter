import random

from . import thongke
from .dongho import chay_mot_lan, uoc_luong_thoi_luong

SO_LAN_KHOI_DONG = 3
SO_LAN_TOI_THIEU = 10
SO_LAN_TOI_DA = 400
BUOC_KIEM = 10
NGAN_SACH_GIAY_MAC_DINH = 30


class MauDo:
    def __init__(self, nhan):
        self.nhan = nhan
        self.thoi_gian = []
        self.so_lan_loi = 0

    def them(self, ket_qua):
        if ket_qua.thanh_cong:
            self.thoi_gian.append(ket_qua.thoi_gian_ns)
        else:
            self.so_lan_loi += 1

    def __len__(self):
        return len(self.thoi_gian)


class KetQuaThiNghiem:
    def __init__(self, mau, so_vong, dung_som, ngan_sach_het):
        self.mau = mau
        self.so_vong = so_vong
        self.dung_som = dung_som
        self.ngan_sach_het = ngan_sach_het

    @property
    def cac_nhan(self):
        return [m.nhan for m in self.mau]


def khoi_dong(cac_lenh, so_lan=SO_LAN_KHOI_DONG):
    """Chay bo may cho nong truoc khi do that.

    Lan chay dau luon cham hon han vi he dieu hanh chua nap file vao
    bo nho dem va CPU chua tang tan so. Bo may lan dau di.
    """
    for _ in range(so_lan):
        for lenh in cac_lenh:
            chay_mot_lan(lenh)


def uoc_luong_so_lan(cac_lenh, ngan_sach_giay):
    """Tinh xem ngan sach thoi gian cho phep do bao nhieu vong."""
    thoi_luong = sum(uoc_luong_thoi_luong(l) for l in cac_lenh)
    if thoi_luong <= 0:
        return SO_LAN_TOI_DA
    uoc = int(ngan_sach_giay * 1_000_000_000 / thoi_luong)
    return max(SO_LAN_TOI_MIN_AN_TOAN(uoc), SO_LAN_TOI_THIEU)


def SO_LAN_TOI_MIN_AN_TOAN(uoc):
    return min(uoc, SO_LAN_TOI_DA)


def da_du_tin(mau, hat_giong):
    """Da phan biet duoc chua - dung de dung som khi ro rang."""
    if len(mau) < 2:
        return False
    goc = mau[0]
    for khac in mau[1:]:
        if len(goc) < SO_LAN_TOI_THIEU or len(khac) < SO_LAN_TOI_THIEU:
            return False
        _, duoi, tren = thongke.khoang_tin_cay_hieu(
            goc.thoi_gian, khac.thoi_gian, hat_giong=hat_giong)
        if not thongke.du_tin_de_ket_luan(duoi, tren):
            return False
    return True


def do_xen_ke(cac_lenh, cac_nhan=None, so_lan=None,
              ngan_sach_giay=NGAN_SACH_GIAY_MAC_DINH,
              hat_giong=None, xao_thu_tu=True, bao_tien_do=None):
    """Do nhieu lenh xen ke nhau trong cung mot vong.

    Do het lenh A roi moi do lenh B thi may co the doi trang thai
    giua chung - nong len, bi tien trinh khac chen vao - va toan bo
    chenh lech do se bi quy nham cho lenh B. Xen ke thi ca hai cung
    chiu mot dieu kien tai moi thoi diem.

    Thu tu trong moi vong con duoc xao ngau nhien de khong lenh nao
    luon duoc chay ngay sau lenh nao.
    """
    cac_nhan = cac_nhan or [f"lenh {i + 1}" for i in range(len(cac_lenh))]
    rng = random.Random(hat_giong)
    mau = [MauDo(n) for n in cac_nhan]

    khoi_dong(cac_lenh)

    if so_lan is None:
        so_lan = uoc_luong_so_lan(cac_lenh, ngan_sach_giay)

    chi_so = list(range(len(cac_lenh)))
    dung_som = False
    vong = 0

    for vong in range(1, so_lan + 1):
        if xao_thu_tu:
            rng.shuffle(chi_so)
        for i in chi_so:
            mau[i].them(chay_mot_lan(cac_lenh[i], cac_nhan[i]))

        if bao_tien_do:
            bao_tien_do(vong, so_lan)

        du_dai = vong >= SO_LAN_TOI_THIEU * 2
        den_moc = vong % BUOC_KIEM == 0
        if du_dai and den_moc and len(mau) > 1:
            if da_du_tin(mau, hat_giong):
                dung_som = True
                break

    return KetQuaThiNghiem(mau, vong, dung_som, vong >= so_lan)


def do_don(lenh, nhan="lenh", so_lan=30, hat_giong=None):
    return do_xen_ke([lenh], [nhan], so_lan=so_lan, hat_giong=hat_giong)

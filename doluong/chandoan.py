import time

from . import thongke

SO_LAN_THU_MAY = 200
VONG_LAP_TAC_VU = 3000
NGUONG_MAY_BAN = 0.15


class TinhTrangMay:
    def __init__(self, do_troi, he_so_bien_thien, phan_giai, tu_tuong_quan,
                 da_kiem=True):
        self.do_troi = do_troi
        self.he_so_bien_thien = he_so_bien_thien
        self.phan_giai = phan_giai
        self.tu_tuong_quan = tu_tuong_quan
        self.da_kiem = da_kiem

    @property
    def dang_ban(self):
        return self.da_kiem and self.do_troi >= NGUONG_MAY_BAN

    @property
    def xep_loai(self):
        if not self.da_kiem:
            return "chua kiem"
        if self.do_troi < 0.05 and self.he_so_bien_thien < 0.10:
            return "yen"
        if self.do_troi < NGUONG_MAY_BAN:
            return "hoi on"
        return "on ao"

    def loi_khuyen(self):
        if not self.da_kiem:
            return "Chua kiem may nen khong biet ket qua dang tin toi dau."
        if self.xep_loai == "yen":
            return "May dang yen, do duoc."
        if self.xep_loai == "hoi on":
            return ("May hoi bien dong. Ket qua van dung nhung "
                    "chenh lech nho co the khong phan biet duoc.")
        return ("May dang ban. Nen dong bot ung dung, cam sac, "
                "roi do lai. Neu van do bay gio thi chi tin "
                "chenh lech lon.")


def tac_vu_chuan():
    tong = 0
    for i in range(VONG_LAP_TAC_VU):
        tong += i * i
    return tong


def do_may(so_lan=SO_LAN_THU_MAY):
    """Do chinh cai may nay, khong do chuong trinh nao ca.

    Chay mot tac vu tinh toan co dinh nhieu lan. Moi chenh lech quan
    sat duoc deu la do may chu khong phai do tac vu, vi tac vu khong
    doi. Tu do biet may nay do duoc chinh xac toi dau.
    """
    mau = []
    for _ in range(so_lan):
        bat_dau = time.perf_counter_ns()
        tac_vu_chuan()
        mau.append(time.perf_counter_ns() - bat_dau)

    return TinhTrangMay(
        do_troi=thongke.do_troi(mau),
        he_so_bien_thien=thongke.he_so_bien_thien(mau),
        phan_giai=thongke.do_phan_giai_kha_di(mau),
        tu_tuong_quan=thongke.tu_tuong_quan(mau),
    )


def kiem_truoc_khi_do():
    return do_may()

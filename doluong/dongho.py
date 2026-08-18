import subprocess
import time

NANO = 1_000_000_000
SO_LAN_UOC_LUONG = 5


class KetQuaChay:
    def __init__(self, nhan, thoi_gian_ns, ma_thoat):
        self.nhan = nhan
        self.thoi_gian_ns = thoi_gian_ns
        self.ma_thoat = ma_thoat

    @property
    def thanh_cong(self):
        return self.ma_thoat == 0


def chay_mot_lan(lenh, nhan=""):
    bat_dau = time.perf_counter_ns()
    xong = subprocess.run(lenh, shell=True, capture_output=True)
    het = time.perf_counter_ns()
    return KetQuaChay(nhan, het - bat_dau, xong.returncode)


def kiem_lenh_chay_duoc(lenh):
    ket_qua = chay_mot_lan(lenh)
    return ket_qua.thanh_cong, ket_qua.thoi_gian_ns


def uoc_luong_thoi_luong(lenh, so_lan=SO_LAN_UOC_LUONG):
    mau = [chay_mot_lan(lenh).thoi_gian_ns for _ in range(so_lan)]
    return sorted(mau)[len(mau) // 2]


def giay(ns):
    return ns / NANO


def doc_duoc(ns):
    s = giay(ns)
    if s >= 1:
        return f"{s:.3f} s"
    if s >= 0.001:
        return f"{s * 1000:.2f} ms"
    return f"{s * 1_000_000:.1f} us"

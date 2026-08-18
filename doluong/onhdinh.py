"""Thu giam nhieu truoc khi do, thay vi chi phat hien roi bao.

Ba bien phap: ghim tien trinh vao mot nhan CPU, nang do uu tien, tat bo
don rac cua Python.

⚠ DO THAT TREN MAY THU (i7-1185G7, Windows, khong quyen quan tri):
    ghim nhan CPU  -> THAT BAI (SetProcessAffinityMask bi tu choi)
    nang uu tien   -> THAT BAI (khong doi duoc do uu tien)
    tat don rac    -> lam duoc, nhung do troi KHONG giam
                      (trung vi 28,8% -> 83,8% qua 5 lan do moi ben)

Ket luan trung thuc: tren may thuong khong co quyen quan tri, ba bien
phap nay gan nhu vo dung. Chung chi giup tren may chuyen dung co quyen
day du. Do la ly do cong cu nay chon huong PHAT HIEN va BAO ro thay vi
hua se lam may on dinh.

Ham van giu lai vi tren may khac co the co tac dung, nhung mac dinh
KHONG bat, va that bai thi bao ro chu khong im lang.
"""
import gc
import os
import platform
import sys


class KetQuaOnDinh:
    def __init__(self):
        self.da_ghim_nhan = False
        self.da_nang_uu_tien = False
        self.da_tat_don_rac = False
        self.loi = []

    @property
    def co_hieu_luc(self):
        return (self.da_ghim_nhan or self.da_nang_uu_tien
                or self.da_tat_don_rac)

    def mo_ta(self):
        lam_duoc = []
        if self.da_ghim_nhan:
            lam_duoc.append("ghim nhan CPU")
        if self.da_nang_uu_tien:
            lam_duoc.append("nang uu tien")
        if self.da_tat_don_rac:
            lam_duoc.append("tat don rac")
        if not lam_duoc:
            return "khong ap dung duoc bien phap nao"
        return ", ".join(lam_duoc)


def ghim_nhan_cpu(nhan=0):
    """Buoc tien trinh chay tren mot nhan co dinh.

    He dieu hanh hay chuyen tien trinh giua cac nhan. Moi lan chuyen la
    mot lan mat bo nho dem, gay ra gia tri lac trong phep do.
    """
    try:
        if hasattr(os, "sched_setaffinity"):
            os.sched_setaffinity(0, {nhan})
            return True, None
        if platform.system() == "Windows":
            import ctypes
            tien_trinh = ctypes.windll.kernel32.GetCurrentProcess()
            mat_na = 1 << nhan
            ok = ctypes.windll.kernel32.SetProcessAffinityMask(
                tien_trinh, mat_na)
            return bool(ok), None if ok else "SetProcessAffinityMask that bai"
        return False, "he dieu hanh khong ho tro"
    except Exception as loi:
        return False, str(loi)


def nang_do_uu_tien():
    """Xin he dieu hanh uu tien tien trinh nay hon."""
    try:
        if platform.system() == "Windows":
            import ctypes
            HIGH_PRIORITY_CLASS = 0x00000080
            tien_trinh = ctypes.windll.kernel32.GetCurrentProcess()
            ok = ctypes.windll.kernel32.SetPriorityClass(
                tien_trinh, HIGH_PRIORITY_CLASS)
            return bool(ok), None if ok else "khong doi duoc do uu tien"
        os.nice(-5)
        return True, None
    except Exception as loi:
        return False, str(loi)


def tat_don_rac():
    """Bo don rac cua Python chay bat chot, tao gia tri lac."""
    try:
        if gc.isenabled():
            gc.disable()
            gc.collect()
            return True, None
        return False, "da tat san"
    except Exception as loi:
        return False, str(loi)


def bat_don_rac_lai():
    try:
        gc.enable()
    except Exception:
        pass


def on_dinh_may(ghim=True, uu_tien=True, don_rac=True, nhan=0):
    ket_qua = KetQuaOnDinh()

    if don_rac:
        ok, loi = tat_don_rac()
        ket_qua.da_tat_don_rac = ok
        if loi and loi != "da tat san":
            ket_qua.loi.append(f"tat don rac: {loi}")

    if ghim:
        ok, loi = ghim_nhan_cpu(nhan)
        ket_qua.da_ghim_nhan = ok
        if loi:
            ket_qua.loi.append(f"ghim nhan: {loi}")

    if uu_tien:
        ok, loi = nang_do_uu_tien()
        ket_qua.da_nang_uu_tien = ok
        if loi:
            ket_qua.loi.append(f"uu tien: {loi}")

    return ket_qua


def tra_lai_binh_thuong():
    bat_don_rac_lai()
    try:
        if hasattr(os, "sched_setaffinity"):
            os.sched_setaffinity(0, set(range(os.cpu_count() or 1)))
    except Exception:
        pass

"""Kiem cong cu bang cac truong hop DA BIET TRUOC dap an.

Cong cu tu do minh thi luon co mui. Cach kiem doc lap la dua vao
nhung truong hop ma dap an dung khong the ban cai:
  - hai mau sinh tu cung mot nguon  -> phai noi KHONG KET LUAN DUOC
  - mot mau cham gap doi ro rang    -> phai noi KET LUAN DUOC
Sau do dem TY LE BAO SAI tren nhieu lan lap.
"""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doluong import thongke

SO_LAN_LAP = 60
SO_MAU = 60
NGUONG_BAO_SAI = 0.10


def sinh_mau(rng, trung_tam, nhieu, so_mau=SO_MAU, troi=0.0):
    """Sinh mau giong du lieu do that: co nhieu, co gia tri lac, co troi."""
    mau = []
    for i in range(so_mau):
        he_so_troi = 1 + troi * (i / so_mau)
        gia_tri = rng.gauss(trung_tam * he_so_troi, nhieu)
        if rng.random() < 0.03:
            gia_tri *= rng.uniform(1.5, 4.0)
        mau.append(max(gia_tri, 1.0))
    return mau


class TestKhongBaoBuaKhiGiongNhau(unittest.TestCase):
    def test_hai_mau_cung_nguon_it_khi_bao_khac(self):
        bao_sai = 0
        for lan in range(SO_LAN_LAP):
            rng = random.Random(lan)
            a = sinh_mau(rng, 1000, 80)
            b = sinh_mau(rng, 1000, 80)
            _, duoi, tren = thongke.khoang_tin_cay_hieu(a, b, hat_giong=lan)
            if thongke.du_tin_de_ket_luan(duoi, tren):
                bao_sai += 1
        ty_le = bao_sai / SO_LAN_LAP
        self.assertLessEqual(
            ty_le, NGUONG_BAO_SAI,
            f"bao sai {ty_le:.1%} khi hai mau cung nguon")

    def test_van_it_bao_sai_khi_may_troi(self):
        """Do XEN KE nen ca hai cung chiu troi -> van khong bao bua."""
        bao_sai = 0
        for lan in range(SO_LAN_LAP):
            rng = random.Random(100 + lan)
            a, b = [], []
            for i in range(SO_MAU):
                he_so = 1 + 0.4 * (i / SO_MAU)
                a.append(rng.gauss(1000 * he_so, 80))
                b.append(rng.gauss(1000 * he_so, 80))
            _, duoi, tren = thongke.khoang_tin_cay_hieu(a, b, hat_giong=lan)
            if thongke.du_tin_de_ket_luan(duoi, tren):
                bao_sai += 1
        ty_le = bao_sai / SO_LAN_LAP
        self.assertLessEqual(
            ty_le, 0.15,
            f"bao sai {ty_le:.1%} khi may troi 40%")


class TestPhatHienDuocKhacBietThat(unittest.TestCase):
    def test_cham_gap_doi_thi_luon_phat_hien(self):
        bo_sot = 0
        for lan in range(SO_LAN_LAP):
            rng = random.Random(200 + lan)
            a = sinh_mau(rng, 1000, 80)
            b = sinh_mau(rng, 2000, 160)
            _, duoi, tren = thongke.khoang_tin_cay_hieu(a, b, hat_giong=lan)
            if not thongke.du_tin_de_ket_luan(duoi, tren):
                bo_sot += 1
        ty_le = bo_sot / SO_LAN_LAP
        self.assertLessEqual(ty_le, 0.05,
                             f"bo sot {ty_le:.1%} khi cham gap doi")

    def test_uoc_luong_ty_le_gan_dung(self):
        rng = random.Random(999)
        a = sinh_mau(rng, 1000, 50, so_mau=300)
        b = sinh_mau(rng, 1500, 75, so_mau=300)
        ty_le, _, _ = thongke.khoang_tin_cay_hieu(a, b, hat_giong=1)
        self.assertGreater(ty_le, 1.3)
        self.assertLess(ty_le, 1.7)


class TestSoSanhVoiCongThucCu(unittest.TestCase):
    """Chung minh cach cu bao sai nhieu hon cach nay."""

    @staticmethod
    def cach_cu_bao_khac(a, b):
        import math
        import statistics
        ma, mb = statistics.fmean(a), statistics.fmean(b)
        sa = statistics.stdev(a) / math.sqrt(len(a))
        sb = statistics.stdev(b) / math.sqrt(len(b))
        return abs(ma - mb) > 1.96 * (sa + sb)

    def test_cach_cu_bao_sai_nhieu_hon(self):
        """Cach cu do TUAN TU: A het roi moi toi B.

        May troi trong luc do nen B roi vao doan may da nong, toan bo
        chenh lech do bi quy nham cho B. Cach moi do XEN KE nen ca hai
        cung chiu mot muc troi tai moi thoi diem.
        """
        cu = moi = 0
        for lan in range(SO_LAN_LAP):
            rng = random.Random(300 + lan)
            tong = SO_MAU * 2
            troi = [1 + 0.4 * (i / tong) for i in range(tong)]

            a_tuan_tu = [rng.gauss(1000 * troi[i], 80)
                         for i in range(SO_MAU)]
            b_tuan_tu = [rng.gauss(1000 * troi[SO_MAU + i], 80)
                         for i in range(SO_MAU)]
            if self.cach_cu_bao_khac(a_tuan_tu, b_tuan_tu):
                cu += 1

            a_xen_ke = [rng.gauss(1000 * troi[2 * i], 80)
                        for i in range(SO_MAU)]
            b_xen_ke = [rng.gauss(1000 * troi[2 * i + 1], 80)
                        for i in range(SO_MAU)]
            _, d, t = thongke.khoang_tin_cay_hieu(a_xen_ke, b_xen_ke,
                                                  hat_giong=lan)
            if thongke.du_tin_de_ket_luan(d, t):
                moi += 1
        self.assertLess(moi, cu,
                        f"cach moi {moi} vs cach cu {cu} - phai it hon")
        print(f"\n    [do tuan tu bao sai {cu}/{SO_LAN_LAP}, "
              f"do xen ke bao sai {moi}/{SO_LAN_LAP}]")


if __name__ == "__main__":
    unittest.main(verbosity=2)

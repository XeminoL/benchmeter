import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doluong import thongke


class TestThongKeCoBan(unittest.TestCase):
    def test_trung_vi_chong_gia_tri_lac(self):
        sach = [100] * 20
        co_lac = sach + [100000]
        self.assertEqual(thongke.trung_vi(sach), 100)
        self.assertEqual(thongke.trung_vi(co_lac), 100)

    def test_do_troi_bang_khong_khi_on_dinh(self):
        deu = [1000] * 200
        self.assertAlmostEqual(thongke.do_troi(deu), 0.0, places=6)

    def test_do_troi_bat_duoc_khi_cham_dan(self):
        tang_dan = [1000 + i * 10 for i in range(200)]
        self.assertGreater(thongke.do_troi(tang_dan), 0.5)

    def test_tu_tuong_quan_bang_khong_khi_ngau_nhien(self):
        rng = random.Random(1)
        ngau_nhien = [rng.gauss(1000, 50) for _ in range(2000)]
        self.assertLess(abs(thongke.tu_tuong_quan(ngau_nhien)), 0.1)

    def test_tu_tuong_quan_cao_khi_phu_thuoc(self):
        mau = [1000]
        rng = random.Random(2)
        for _ in range(2000):
            mau.append(mau[-1] * 0.9 + 100 + rng.gauss(0, 1))
        self.assertGreater(thongke.tu_tuong_quan(mau), 0.5)


class TestKhoangTinCay(unittest.TestCase):
    def test_hai_mau_giong_het_thi_khoang_chua_mot(self):
        mau = [100 + (i % 7) for i in range(120)]
        _, duoi, tren = thongke.khoang_tin_cay_hieu(mau, list(mau),
                                                    hat_giong=3)
        self.assertLessEqual(duoi, 1.0)
        self.assertGreaterEqual(tren, 1.0)
        self.assertFalse(thongke.du_tin_de_ket_luan(duoi, tren))

    def test_khac_biet_ro_thi_ket_luan_duoc(self):
        cham = [200 + (i % 5) for i in range(120)]
        nhanh = [100 + (i % 5) for i in range(120)]
        ty_le, duoi, tren = thongke.khoang_tin_cay_hieu(cham, nhanh,
                                                        hat_giong=3)
        self.assertTrue(thongke.du_tin_de_ket_luan(duoi, tren))
        self.assertLess(ty_le, 1.0)

    def test_khoang_hep_lai_khi_them_mau(self):
        rng = random.Random(5)

        def be_rong(n):
            a = [rng.gauss(1000, 100) for _ in range(n)]
            b = [rng.gauss(1000, 100) for _ in range(n)]
            _, d, t = thongke.khoang_tin_cay_hieu(a, b, hat_giong=9)
            return t - d

        self.assertLess(be_rong(400), be_rong(30))


class TestPhanGiai(unittest.TestCase):
    def test_may_yen_phan_giai_tot_hon_may_on(self):
        rng = random.Random(11)
        yen = [rng.gauss(1000, 5) for _ in range(300)]
        on = [rng.gauss(1000, 200) for _ in range(300)]
        self.assertLess(thongke.do_phan_giai_kha_di(yen),
                        thongke.do_phan_giai_kha_di(on))

    def test_muc_do_tin_ha_khi_may_troi(self):
        self.assertEqual(thongke.muc_do_tin(0.01, 200, 0.05), "cao")
        self.assertEqual(thongke.muc_do_tin(0.30, 200, 0.05), "thap")


if __name__ == "__main__":
    unittest.main(verbosity=2)

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doluong import chandoan, dothinghiem, ketluan, lichsu, thongke

LENH_NHANH = "python -c pass"


class TestDoXenKe(unittest.TestCase):
    def test_moi_lenh_duoc_do_du_so_vong(self):
        ket_qua = dothinghiem.do_xen_ke(
            [LENH_NHANH, LENH_NHANH], ["a", "b"], so_lan=12, hat_giong=1)
        self.assertEqual(len(ket_qua.mau), 2)
        for mau in ket_qua.mau:
            self.assertEqual(len(mau), ket_qua.so_vong)

    def test_lenh_loi_duoc_dem_rieng(self):
        ket_qua = dothinghiem.do_xen_ke(
            [LENH_NHANH, "python -c \"raise SystemExit(1)\""],
            ["ok", "loi"], so_lan=10, hat_giong=1)
        self.assertEqual(ket_qua.mau[0].so_lan_loi, 0)
        self.assertEqual(ket_qua.mau[1].so_lan_loi, 10)
        self.assertEqual(len(ket_qua.mau[1]), 0)

    def test_hat_giong_giong_nhau_cho_thu_tu_giong_nhau(self):
        import random
        a = random.Random(7)
        b = random.Random(7)
        chi_so = [0, 1, 2]
        x, y = list(chi_so), list(chi_so)
        a.shuffle(x)
        b.shuffle(y)
        self.assertEqual(x, y)

    def test_do_don_chay_duoc(self):
        ket_qua = dothinghiem.do_don(LENH_NHANH, so_lan=8, hat_giong=2)
        self.assertEqual(len(ket_qua.mau), 1)
        self.assertGreater(len(ket_qua.mau[0]), 0)


class TestChanDoanMay(unittest.TestCase):
    def test_do_may_tra_ve_du_chi_so(self):
        tinh_trang = chandoan.do_may(so_lan=60)
        self.assertGreaterEqual(tinh_trang.do_troi, 0)
        self.assertGreater(tinh_trang.phan_giai, 0)
        self.assertIn(tinh_trang.xep_loai, ("yen", "hoi on", "on ao"))
        self.assertTrue(tinh_trang.loi_khuyen())

    def test_chua_kiem_thi_khong_gia_vo_biet(self):
        tinh_trang = chandoan.TinhTrangMay(0, 0, 0, 0, da_kiem=False)
        self.assertEqual(tinh_trang.xep_loai, "chua kiem")
        self.assertFalse(tinh_trang.dang_ban)


class TestBaoCao(unittest.TestCase):
    def _bao_cao_gia(self, mau_a, mau_b):
        ket_qua = dothinghiem.KetQuaThiNghiem(
            mau=[self._mau("a", mau_a), self._mau("b", mau_b)],
            so_vong=len(mau_a), dung_som=False, ngan_sach_het=True)
        may = chandoan.TinhTrangMay(0.02, 0.05, 0.01, 0.0)
        return ketluan.phan_tich(ket_qua, may, hat_giong=1)

    @staticmethod
    def _mau(nhan, thoi_gian):
        m = dothinghiem.MauDo(nhan)
        m.thoi_gian = list(thoi_gian)
        return m

    def test_giong_nhau_thi_khong_ket_luan(self):
        mau = [1000 + (i % 11) for i in range(80)]
        bao_cao = self._bao_cao_gia(mau, list(mau))
        self.assertFalse(bao_cao.co_ket_luan)
        self.assertIn("CHUA KET LUAN DUOC", ketluan.in_bao_cao(bao_cao))

    def test_khac_ro_thi_ket_luan_va_dung_huong(self):
        a = [2000 + (i % 7) for i in range(80)]
        b = [1000 + (i % 7) for i in range(80)]
        bao_cao = self._bao_cao_gia(a, b)
        self.assertTrue(bao_cao.co_ket_luan)
        self.assertTrue(bao_cao.cac_so_sanh[0].nhanh_hon)
        self.assertIn("nhanh hon", ketluan.in_bao_cao(bao_cao))

    def test_bao_cao_noi_ro_khi_chua_kiem_may(self):
        mau = [1000 + (i % 11) for i in range(60)]
        ket_qua = dothinghiem.KetQuaThiNghiem(
            mau=[self._mau("a", mau), self._mau("b", mau)],
            so_vong=60, dung_som=False, ngan_sach_het=True)
        may = chandoan.TinhTrangMay(0, 0, 0, 0, da_kiem=False)
        bao_cao = ketluan.phan_tich(ket_qua, may, hat_giong=1)
        self.assertIn("chua kiem", ketluan.in_bao_cao(bao_cao))


class TestNguongAnToan(unittest.TestCase):
    def test_khoang_vua_cham_mot_thi_khong_ket_luan(self):
        self.assertFalse(thongke.du_tin_de_ket_luan(1.000, 1.05))
        self.assertFalse(thongke.du_tin_de_ket_luan(0.95, 1.000))

    def test_khoang_cach_xa_mot_thi_ket_luan(self):
        self.assertTrue(thongke.du_tin_de_ket_luan(1.02, 1.10))
        self.assertTrue(thongke.du_tin_de_ket_luan(0.90, 0.98))


class TestLichSu(unittest.TestCase):
    def test_ghi_roi_doc_lai_duoc(self):
        import tempfile
        mau = [1000] * 40
        ket_qua = dothinghiem.KetQuaThiNghiem(
            mau=[TestBaoCao._mau("a", mau)], so_vong=40,
            dung_som=False, ngan_sach_het=True)
        may = chandoan.TinhTrangMay(0.02, 0.05, 0.01, 0.0)
        bao_cao = ketluan.phan_tich(ket_qua, may, hat_giong=1)
        with tempfile.TemporaryDirectory() as thu_muc:
            lichsu.ghi(bao_cao, "thu", thu_muc)
            doc_lai = lichsu.doc(thu_muc)
            self.assertEqual(len(doc_lai), 1)
            self.assertEqual(doc_lai[0]["ghi_chu"], "thu")

    def test_canh_bao_khi_may_khac_han(self):
        import tempfile
        mau = [1000] * 40
        may_yen = chandoan.TinhTrangMay(0.01, 0.05, 0.01, 0.0)
        may_on = chandoan.TinhTrangMay(0.40, 0.20, 0.05, 0.0)
        ket_qua = dothinghiem.KetQuaThiNghiem(
            mau=[TestBaoCao._mau("a", mau)], so_vong=40,
            dung_som=False, ngan_sach_het=True)
        with tempfile.TemporaryDirectory() as thu_muc:
            lichsu.ghi(ketluan.phan_tich(ket_qua, may_yen, hat_giong=1),
                       "", thu_muc)
            sau = ketluan.phan_tich(ket_qua, may_on, hat_giong=1)
            so_sanh = lichsu.so_voi_lan_truoc(sau, thu_muc)
            self.assertTrue(so_sanh["may_khac"])
            self.assertIn("CANH BAO", lichsu.in_so_sanh(so_sanh))


if __name__ == "__main__":
    unittest.main(verbosity=2)

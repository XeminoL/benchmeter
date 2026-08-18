import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from doluong import onhdinh


class TestOnDinh(unittest.TestCase):
    def tearDown(self):
        onhdinh.tra_lai_binh_thuong()

    def test_that_bai_thi_bao_ro_chu_khong_im_lang(self):
        ket_qua = onhdinh.on_dinh_may()
        lam_duoc = (ket_qua.da_ghim_nhan or ket_qua.da_nang_uu_tien
                    or ket_qua.da_tat_don_rac)
        if not lam_duoc:
            self.assertTrue(ket_qua.loi,
                            "khong lam duoc gi ma cung khong bao loi")

    def test_mo_ta_luon_doc_duoc(self):
        ket_qua = onhdinh.on_dinh_may()
        self.assertIsInstance(ket_qua.mo_ta(), str)
        self.assertTrue(ket_qua.mo_ta())

    def test_tra_lai_binh_thuong_bat_lai_don_rac(self):
        import gc
        onhdinh.tat_don_rac()
        onhdinh.tra_lai_binh_thuong()
        self.assertTrue(gc.isenabled())

    def test_khong_nem_loi_khi_khong_du_quyen(self):
        try:
            onhdinh.on_dinh_may()
            onhdinh.tra_lai_binh_thuong()
        except Exception as loi:
            self.fail(f"khong duoc nem loi ra ngoai: {loi}")


if __name__ == "__main__":
    unittest.main(verbosity=2)

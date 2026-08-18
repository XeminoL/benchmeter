"""Luu ket qua do de so sanh theo thoi gian.

Do hom nay so voi tuan truoc thi vuong mot cai bay: may hom nay va may
tuan truoc khong giong nhau. Neu chi so hai con so tho thi may doi se
bi nham thanh chuong trinh doi.

Cach tranh: luu kem tinh trang may luc do. Khi so, neu hai lan do co
tinh trang may khac han nhau thi bao ro thay vi ket luan bua.
"""
import json
import time
from pathlib import Path

from . import thongke

TEN_FILE = "lichsu-doluong.json"
NGUONG_MAY_KHAC_NHAU = 0.10


def _duong_dan(thu_muc=None):
    goc = Path(thu_muc) if thu_muc else Path.cwd()
    return goc / TEN_FILE


def doc(thu_muc=None):
    duong_dan = _duong_dan(thu_muc)
    if not duong_dan.exists():
        return []
    try:
        return json.loads(duong_dan.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def ghi(bao_cao, ghi_chu="", thu_muc=None):
    ban_ghi = {
        "thoi_diem": time.time(),
        "ghi_chu": ghi_chu,
        "may": {
            "do_troi": bao_cao.tinh_trang_may.do_troi,
            "phan_giai": bao_cao.tinh_trang_may.phan_giai,
            "bien_thien": bao_cao.tinh_trang_may.he_so_bien_thien,
        },
        "ket_qua": [
            {
                "nhan": m.nhan,
                "trung_vi_ns": thongke.trung_vi(m.thoi_gian),
                "so_mau": len(m),
            }
            for m in bao_cao.ket_qua.mau
        ],
    }
    cu = doc(thu_muc)
    cu.append(ban_ghi)
    _duong_dan(thu_muc).write_text(
        json.dumps(cu, indent=2, ensure_ascii=False), encoding="utf-8")
    return ban_ghi


def so_voi_lan_truoc(bao_cao, thu_muc=None):
    """So voi ban ghi gan nhat, canh bao neu may da khac di."""
    cu = doc(thu_muc)
    if not cu:
        return None

    truoc = cu[-1]
    hien_tai = {m.nhan: thongke.trung_vi(m.thoi_gian)
                for m in bao_cao.ket_qua.mau}
    truoc_map = {r["nhan"]: r["trung_vi_ns"] for r in truoc["ket_qua"]}

    chung = set(hien_tai) & set(truoc_map)
    if not chung:
        return None

    troi_truoc = truoc["may"]["do_troi"]
    troi_nay = bao_cao.tinh_trang_may.do_troi
    may_khac = abs(troi_nay - troi_truoc) > NGUONG_MAY_KHAC_NHAU

    thay_doi = []
    for nhan in sorted(chung):
        cu_ns = truoc_map[nhan]
        moi_ns = hien_tai[nhan]
        if cu_ns:
            thay_doi.append((nhan, (moi_ns - cu_ns) / cu_ns * 100))

    return {
        "may_khac": may_khac,
        "troi_truoc": troi_truoc,
        "troi_nay": troi_nay,
        "thay_doi": thay_doi,
        "thoi_diem_truoc": truoc["thoi_diem"],
    }


def in_so_sanh(ket_qua_so):
    if not ket_qua_so:
        return ""
    dong = ["", "SO VOI LAN DO TRUOC", "-" * 56]
    for nhan, phan_tram in ket_qua_so["thay_doi"]:
        huong = "cham hon" if phan_tram > 0 else "nhanh hon"
        dong.append(f"  {nhan:<28} {huong} {abs(phan_tram):.1f}%")
    if ket_qua_so["may_khac"]:
        dong.append("")
        dong.append(f"  CANH BAO: may luc do khac han lan truoc")
        dong.append(f"  (troi {ket_qua_so['troi_truoc'] * 100:.0f}% "
                    f"-> {ket_qua_so['troi_nay'] * 100:.0f}%)")
        dong.append("  Chenh lech tren co the do may, khong do chuong trinh.")
    dong.append("")
    return "\n".join(dong)

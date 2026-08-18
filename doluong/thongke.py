import math
import random
import statistics

SO_LAN_BOOTSTRAP = 2000
MUC_TIN_CAY = 0.95
NGUONG_TROI_CAO = 0.20
NGUONG_TROI_VUA = 0.08
SO_KHOI_TOI_THIEU = 4


def trung_vi(mau):
    return statistics.median(mau)


def do_lech_tuyet_doi_trung_vi(mau):
    tv = trung_vi(mau)
    return statistics.median([abs(x - tv) for x in mau])


def khoang_tin_cay_bootstrap(mau, muc=MUC_TIN_CAY, so_lan=SO_LAN_BOOTSTRAP,
                             hat_giong=None):
    if len(mau) < 2:
        return (mau[0], mau[0]) if mau else (0, 0)
    rng = random.Random(hat_giong)
    n = len(mau)
    lap = sorted(statistics.median(rng.choices(mau, k=n))
                 for _ in range(so_lan))
    duoi = (1 - muc) / 2
    return lap[int(duoi * so_lan)], lap[int((1 - duoi) * so_lan) - 1]


def khoang_tin_cay_hieu(mau_a, mau_b, muc=MUC_TIN_CAY,
                        so_lan=SO_LAN_BOOTSTRAP, hat_giong=None):
    """Khoang tin cay cua ty le b/a, lay tung cap da ghep doi.

    Ghep doi vi hai lenh do XEN KE nen lan thu i cua ca hai chiu
    cung dieu kien may. Bootstrap tren cap giu nguyen su ghep do.
    """
    rng = random.Random(hat_giong)
    cap = list(zip(mau_a, mau_b))
    n = len(cap)
    if n < 2:
        return 0.0, 0.0, 0.0
    ty_le = []
    for _ in range(so_lan):
        chon = rng.choices(cap, k=n)
        ta = statistics.median([c[0] for c in chon])
        tb = statistics.median([c[1] for c in chon])
        ty_le.append(tb / ta if ta else 1.0)
    ty_le.sort()
    duoi = (1 - muc) / 2
    goc = trung_vi(mau_b) / trung_vi(mau_a) if trung_vi(mau_a) else 1.0
    return goc, ty_le[int(duoi * so_lan)], ty_le[int((1 - duoi) * so_lan) - 1]


def do_troi(mau, so_khoi=8):
    """May co on dinh trong luc do khong.

    Cat mau thanh cac khoi theo thu tu thoi gian, so trung vi khoi
    cao nhat voi thap nhat. Tra ve ty le troi.
    """
    if len(mau) < so_khoi * 2:
        so_khoi = max(2, len(mau) // 2)
    kich_thuoc = len(mau) // so_khoi
    if kich_thuoc < 1:
        return 0.0
    khoi = [trung_vi(mau[i * kich_thuoc:(i + 1) * kich_thuoc])
            for i in range(so_khoi)]
    khoi = [k for k in khoi if k > 0]
    if len(khoi) < SO_KHOI_TOI_THIEU:
        return 0.0
    return (max(khoi) - min(khoi)) / min(khoi)


def tu_tuong_quan(mau, tre=1):
    n = len(mau)
    if n <= tre + 1:
        return 0.0
    tb = statistics.fmean(mau)
    tu = sum((mau[i] - tb) * (mau[i + tre] - tb) for i in range(n - tre))
    mau_so = sum((x - tb) ** 2 for x in mau)
    return tu / mau_so if mau_so else 0.0


def he_so_bien_thien(mau):
    tv = trung_vi(mau)
    if not tv:
        return 0.0
    return do_lech_tuyet_doi_trung_vi(mau) * 1.4826 / tv


def do_phan_giai_kha_di(mau):
    """Chenh lech nho nhat may nay phan biet duoc, theo ty le.

    Dua tren sai so chuan cua trung vi: 1.253 * sigma / sqrt(n),
    nhan 2 vi so hai ben, nhan 1.96 cho muc 95%.
    """
    n = len(mau)
    if n < 2:
        return float("inf")
    sigma = do_lech_tuyet_doi_trung_vi(mau) * 1.4826
    tv = trung_vi(mau)
    if not tv:
        return float("inf")
    sai_so_chuan = 1.253 * sigma / math.sqrt(n)
    return 1.96 * math.sqrt(2) * sai_so_chuan / tv


BIEN_AN_TOAN = 0.005


def du_tin_de_ket_luan(can_duoi, can_tren, bien=BIEN_AN_TOAN):
    """Khoang tin cay cua ty le co nam han mot ben cua 1.0 khong.

    Doi hoi cach 1.0 mot khoang nho thay vi chi vua cham. Khoang chi
    vua sat 1.0 nghia la ket luan phu thuoc vao vai mau, do lai lan
    nua rat de dao chieu.
    """
    return can_duoi > 1.0 + bien or can_tren < 1.0 - bien


def muc_do_tin(troi, so_mau, he_so_bt):
    if troi >= NGUONG_TROI_CAO or he_so_bt > 0.5:
        return "thap"
    if troi >= NGUONG_TROI_VUA or so_mau < 30:
        return "trung binh"
    return "cao"

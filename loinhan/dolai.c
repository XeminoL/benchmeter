/* Do lai bang C de tach nhieu do Python gay ra.
 *
 * Python co bo don rac va lop thong dich, ban than chung tao nhieu.
 * Neu con so do trong C van giong trong Python thi nhieu la do MAY,
 * khong phai do Python. Do la dieu can chung minh.
 *
 * Bien dich: gcc -O2 -o dolai dolai.c
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define SO_LAN_MAC_DINH 30000
#define VONG_LAP_TAC_VU 3000
#define NHAN_TOI_THIEU 50
#define KICH_THUOC_KHOI 300
#define KICH_THUOC_DOAN 40
#define SO_CAP_KIEM 150
#define Z95 1.959964

/* volatile de trinh bien dich KHONG duoc xoa vong lap.
 *
 * Bay kinh dien khi do hieu nang bang C: voi -O2 trinh bien dich thay
 * ket qua khong ai dung nen xoa sach vong lap, do ra 0 ns. Doc gia tri
 * qua bien volatile buoc no phai chay that.
 */
static volatile long long ket_qua_chan;

/* Tham so `hat` doi moi lan goi nen trinh bien dich khong the tinh san
 * ket qua. Khong co no, -O2 se thay moi lan goi deu ra cung mot so va
 * chi chay dung mot lan, do ra 0 ns.
 */
static long long tac_vu(int hat) {
    long long tong = 0;
    for (int i = 0; i < VONG_LAP_TAC_VU; i++) {
        tong += (long long)(i ^ hat) * i;
    }
    ket_qua_chan = tong;
    return tong;
}

static long long dong_ho_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static int so_sanh_ll(const void *a, const void *b) {
    long long x = *(const long long *)a;
    long long y = *(const long long *)b;
    return (x > y) - (x < y);
}

static double trung_vi(long long *mau, int n) {
    long long *ban_sao = malloc((size_t)n * sizeof(long long));
    memcpy(ban_sao, mau, (size_t)n * sizeof(long long));
    qsort(ban_sao, (size_t)n, sizeof(long long), so_sanh_ll);
    double kq = (n % 2) ? (double)ban_sao[n / 2]
                        : (ban_sao[n / 2 - 1] + ban_sao[n / 2]) / 2.0;
    free(ban_sao);
    return kq;
}

static double trung_binh(long long *mau, int n) {
    double tong = 0;
    for (int i = 0; i < n; i++) tong += (double)mau[i];
    return tong / n;
}

static double do_lech_chuan(long long *mau, int n) {
    double tb = trung_binh(mau, n);
    double tong = 0;
    for (int i = 0; i < n; i++) {
        double d = (double)mau[i] - tb;
        tong += d * d;
    }
    return (n > 1) ? sqrt(tong / (n - 1)) : 0.0;
}

/* Cach cu: cong thuc chia can N */
static int cach_cu_bao_khac(long long *a, int na, long long *b, int nb) {
    double ma = trung_binh(a, na), mb = trung_binh(b, nb);
    double sa = do_lech_chuan(a, na) / sqrt((double)na);
    double sb = do_lech_chuan(b, nb) / sqrt((double)nb);
    double lech = fabs(ma - mb);
    return lech > Z95 * (sa + sb);
}

int main(int argc, char **argv) {
    int so_lan = (argc > 1) ? atoi(argv[1]) : SO_LAN_MAC_DINH;
    if (so_lan < 1000) so_lan = 1000;

    long long *mau = malloc((size_t)so_lan * sizeof(long long));
    if (!mau) return 1;

    printf("\nDO LAI BANG C (tach nhieu do Python)\n");
    printf("======================================================\n");

    long long t_thu = dong_ho_ns();
    long long buoc_nho_nhat = 0;
    for (int i = 0; i < 1000000; i++) {
        long long t = dong_ho_ns();
        if (t > t_thu) {
            buoc_nho_nhat = t - t_thu;
            break;
        }
    }
    printf("do phan giai dong ho: %lld ns\n", buoc_nho_nhat);
    if (buoc_nho_nhat > 1000) {
        printf("CANH BAO: dong ho tho hon 1 us, ket qua co the khong tin\n");
    }
    printf("Do %d lan...\n\n", so_lan);

    volatile long long chan = 0;
    for (int i = 0; i < 200; i++) chan += tac_vu(i);

    /* Tac vu phai du nang de vuot do phan giai dong ho.
     *
     * Dong ho buoc 100 ns ma tac vu chi mat 50 ns thi phan lon phep do
     * ra 0. Phai lap tac vu nhieu lan trong mot phep do cho du lau.
     * Day dung la bai hoc "biet gioi han dung cu do" cua vat ly.
     */
    long long t0_thu = dong_ho_ns();
    for (int i = 0; i < 100; i++) chan += tac_vu(i);
    long long mot_lan = (dong_ho_ns() - t0_thu) / 100;

    int so_lap = 1;
    if (mot_lan > 0) {
        while (mot_lan * so_lap < buoc_nho_nhat * NHAN_TOI_THIEU)
            so_lap *= 2;
    } else {
        so_lap = 1024;
    }
    printf("moi phep do lap tac vu %d lan (de vuot do phan giai)\n\n",
           so_lap);

    for (int i = 0; i < so_lan; i++) {
        long long t0 = dong_ho_ns();
        for (int k = 0; k < so_lap; k++) chan += tac_vu(i + k);
        mau[i] = (dong_ho_ns() - t0) / so_lap;
    }

    int so_khoi = so_lan / KICH_THUOC_KHOI;
    double thap = 1e18, cao = 0;
    for (int k = 0; k < so_khoi; k++) {
        double tv = trung_vi(mau + k * KICH_THUOC_KHOI, KICH_THUOC_KHOI);
        if (tv < thap) thap = tv;
        if (tv > cao) cao = tv;
    }

    printf("1. MAY CO TROI KHONG\n");
    printf("------------------------------------------------------\n");
    printf("   khoi nhanh nhat : %.0f ns\n", thap);
    printf("   khoi cham nhat  : %.0f ns\n", cao);
    printf("   chenh lech      : %.1f%%\n", (cao - thap) / thap * 100);

    int sai_tuan_tu = 0, tong_tuan_tu = 0;
    int buoc = KICH_THUOC_DOAN * 2;
    for (int i = 0; i + buoc < so_lan && tong_tuan_tu < SO_CAP_KIEM;
         i += buoc) {
        tong_tuan_tu++;
        if (cach_cu_bao_khac(mau + i, KICH_THUOC_DOAN,
                             mau + i + KICH_THUOC_DOAN, KICH_THUOC_DOAN))
            sai_tuan_tu++;
    }

    printf("\n2. CACH CU (chia can N, do tuan tu)\n");
    printf("------------------------------------------------------\n");
    printf("   bao 'khac nhau' %d/%d = %.1f%%\n", sai_tuan_tu, tong_tuan_tu,
           100.0 * sai_tuan_tu / tong_tuan_tu);
    printf("   -> deu SAI, vi hai ben la cung mot tac vu\n");

    /* Xen ke: lay chan/le tu cung cua so */
    long long a[KICH_THUOC_DOAN], b[KICH_THUOC_DOAN];
    int sai_xen_ke = 0, tong_xen_ke = 0;
    for (int i = 0; i + buoc < so_lan && tong_xen_ke < SO_CAP_KIEM;
         i += buoc) {
        for (int j = 0; j < KICH_THUOC_DOAN; j++) {
            a[j] = mau[i + 2 * j];
            b[j] = mau[i + 2 * j + 1];
        }
        tong_xen_ke++;
        if (cach_cu_bao_khac(a, KICH_THUOC_DOAN, b, KICH_THUOC_DOAN))
            sai_xen_ke++;
    }

    printf("\n3. XEN KE (cung cong thuc, chi doi CACH DO)\n");
    printf("------------------------------------------------------\n");
    printf("   bao 'khac nhau' %d/%d = %.1f%%\n", sai_xen_ke, tong_xen_ke,
           100.0 * sai_xen_ke / tong_xen_ke);

    printf("\n======================================================\n");
    printf("   Trong C, khong co bo don rac, khong co lop thong dich.\n");
    printf("   Neu van thay troi va van thay bao sai, thi nguyen nhan\n");
    printf("   la MAY chu khong phai ngon ngu.\n\n");

    free(mau);
    return (int)(chan & 0);
}

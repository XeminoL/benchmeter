#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define DEFAULT_RUNS 20000
#define TASK_ITERATIONS 3000
#define MIN_CLOCK_MULTIPLE 50
#define BLOCK_SIZE 300
#define WINDOW_SIZE 40
#define MAX_PAIRS 150
#define Z95 1.959964
#define CALIBRATION_RUNS 100
#define WARMUP_RUNS 200

static volatile long long sink;

static long long task(int seed) {
    long long total = 0;
    for (int i = 0; i < TASK_ITERATIONS; i++) {
        total += (long long)(i ^ seed) * i;
    }
    sink = total;
    return total;
}

static long long now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static int compare_ll(const void *a, const void *b) {
    long long x = *(const long long *)a;
    long long y = *(const long long *)b;
    return (x > y) - (x < y);
}

static double median(long long *samples, int count) {
    long long *copy = malloc((size_t)count * sizeof(long long));
    memcpy(copy, samples, (size_t)count * sizeof(long long));
    qsort(copy, (size_t)count, sizeof(long long), compare_ll);
    double result = (count % 2)
        ? (double)copy[count / 2]
        : (copy[count / 2 - 1] + copy[count / 2]) / 2.0;
    free(copy);
    return result;
}

static double mean(long long *samples, int count) {
    double total = 0;
    for (int i = 0; i < count; i++) total += (double)samples[i];
    return total / count;
}

static double standard_deviation(long long *samples, int count) {
    double average = mean(samples, count);
    double total = 0;
    for (int i = 0; i < count; i++) {
        double delta = (double)samples[i] - average;
        total += delta * delta;
    }
    return (count > 1) ? sqrt(total / (count - 1)) : 0.0;
}

static int classical_test_says_different(long long *left, int left_count,
                                         long long *right, int right_count) {
    double left_error = standard_deviation(left, left_count)
        / sqrt((double)left_count);
    double right_error = standard_deviation(right, right_count)
        / sqrt((double)right_count);
    double difference = fabs(mean(left, left_count) - mean(right, right_count));
    return difference > Z95 * (left_error + right_error);
}

static long long clock_resolution_ns(void) {
    long long start = now_ns();
    for (int i = 0; i < 1000000; i++) {
        long long current = now_ns();
        if (current > start) return current - start;
    }
    return 0;
}

static int calibrate_repeats(long long resolution) {
    long long start = now_ns();
    for (int i = 0; i < CALIBRATION_RUNS; i++) sink += task(i);
    long long per_call = (now_ns() - start) / CALIBRATION_RUNS;

    if (per_call <= 0) return 1024;

    int repeats = 1;
    while (per_call * repeats < resolution * MIN_CLOCK_MULTIPLE) repeats *= 2;
    return repeats;
}

int main(int argc, char **argv) {
    int runs = (argc > 1) ? atoi(argv[1]) : DEFAULT_RUNS;
    if (runs < 1000) runs = DEFAULT_RUNS;

    long long *samples = malloc((size_t)runs * sizeof(long long));
    if (!samples) return 1;

    printf("\nVERIFICATION IN C\n");
    printf("======================================================\n");

    long long resolution = clock_resolution_ns();
    printf("clock resolution: %lld ns\n", resolution);
    if (resolution > 1000) {
        printf("WARNING: clock coarser than 1 us, results may be unreliable\n");
    }

    for (int i = 0; i < WARMUP_RUNS; i++) sink += task(i);

    int repeats = calibrate_repeats(resolution);
    printf("each sample repeats the task %d times to clear the clock\n\n",
           repeats);
    printf("collecting %d samples...\n\n", runs);

    for (int i = 0; i < runs; i++) {
        long long start = now_ns();
        for (int k = 0; k < repeats; k++) sink += task(i + k);
        samples[i] = (now_ns() - start) / repeats;
    }

    int blocks = runs / BLOCK_SIZE;
    double fastest = 1e18, slowest = 0;
    for (int b = 0; b < blocks; b++) {
        double value = median(samples + b * BLOCK_SIZE, BLOCK_SIZE);
        if (value < fastest) fastest = value;
        if (value > slowest) slowest = value;
    }

    printf("1. DOES THE MACHINE DRIFT?\n");
    printf("------------------------------------------------------\n");
    printf("   fastest block : %.0f ns\n", fastest);
    printf("   slowest block : %.0f ns\n", slowest);
    printf("   difference    : %.1f%%\n", (slowest - fastest) / fastest * 100);

    int step = WINDOW_SIZE * 2;
    int sequential_errors = 0, sequential_trials = 0;
    for (int i = 0; i + step < runs && sequential_trials < MAX_PAIRS;
         i += step) {
        sequential_trials++;
        if (classical_test_says_different(samples + i, WINDOW_SIZE,
                                          samples + i + WINDOW_SIZE,
                                          WINDOW_SIZE)) {
            sequential_errors++;
        }
    }

    printf("\n2. MEASURED ONE AFTER THE OTHER\n");
    printf("------------------------------------------------------\n");
    printf("   reported a difference %d/%d = %.1f%%\n",
           sequential_errors, sequential_trials,
           100.0 * sequential_errors / sequential_trials);
    printf("   -> all wrong; both halves are the same task\n");

    long long left[WINDOW_SIZE], right[WINDOW_SIZE];
    int interleaved_errors = 0, interleaved_trials = 0;
    for (int i = 0; i + step < runs && interleaved_trials < MAX_PAIRS;
         i += step) {
        for (int j = 0; j < WINDOW_SIZE; j++) {
            left[j] = samples[i + 2 * j];
            right[j] = samples[i + 2 * j + 1];
        }
        interleaved_trials++;
        if (classical_test_says_different(left, WINDOW_SIZE,
                                          right, WINDOW_SIZE)) {
            interleaved_errors++;
        }
    }

    printf("\n3. MEASURED ALTERNATELY\n");
    printf("------------------------------------------------------\n");
    printf("   reported a difference %d/%d = %.1f%%\n",
           interleaved_errors, interleaved_trials,
           100.0 * interleaved_errors / interleaved_trials);

    printf("\n======================================================\n");
    printf("   C has no garbage collector and no interpreter.\n");
    printf("   The drift and the false positives are the machine,\n");
    printf("   not the language.\n\n");

    free(samples);
    return 0;
}

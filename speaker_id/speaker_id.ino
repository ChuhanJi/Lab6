#include <Lab6_inferencing.h>
#include <driver/i2s.h>

// ── Pin definitions ──────────────────────────────────────────────────────────
#define I2S_SCK   D1
#define I2S_WS    D2
#define I2S_SD    D0
#define LED_PIN   D3

// ── Tunable parameters ───────────────────────────────────────────────────────
#define CONFIDENCE_THRESHOLD  0.60f   // below this → reject as Unknown
#define AUDIO_GAIN            8       // match gain used during data collection
#define SLEEP_MS              3000    // ms to wait between inferences (battery saving)

// ── Audio buffer ─────────────────────────────────────────────────────────────
static int16_t inference_buffer[EI_CLASSIFIER_RAW_SAMPLE_COUNT];

// ── I2S init ─────────────────────────────────────────────────────────────────
static void i2s_init() {
    i2s_config_t cfg = {
        .mode                 = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
        .sample_rate          = EI_CLASSIFIER_FREQUENCY,
        .bits_per_sample      = I2S_BITS_PER_SAMPLE_32BIT,
        .channel_format       = I2S_CHANNEL_FMT_ONLY_LEFT,
        .communication_format = I2S_COMM_FORMAT_STAND_I2S,
        .intr_alloc_flags     = ESP_INTR_FLAG_LEVEL1,
        .dma_buf_count        = 8,
        .dma_buf_len          = 512,
        .use_apll             = false,
    };
    i2s_pin_config_t pins = {
        .bck_io_num   = I2S_SCK,
        .ws_io_num    = I2S_WS,
        .data_out_num = I2S_PIN_NO_CHANGE,
        .data_in_num  = I2S_SD,
    };
    i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL);
    i2s_set_pin(I2S_NUM_0, &pins);
}

// ── Record EI_CLASSIFIER_RAW_SAMPLE_COUNT samples into inference_buffer ──────
static void record_audio() {
    int32_t tmp[256];
    int collected = 0;
    while (collected < EI_CLASSIFIER_RAW_SAMPLE_COUNT) {
        size_t bytes_read;
        int want = min(256, EI_CLASSIFIER_RAW_SAMPLE_COUNT - collected);
        i2s_read(I2S_NUM_0, tmp, want * sizeof(int32_t), &bytes_read, portMAX_DELAY);
        int got = bytes_read / sizeof(int32_t);
        for (int i = 0; i < got && collected < EI_CLASSIFIER_RAW_SAMPLE_COUNT; i++) {
            int32_t s = (int32_t)((int16_t)(tmp[i] >> 16)) * AUDIO_GAIN;
            if (s >  32767) s =  32767;
            if (s < -32768) s = -32768;
            inference_buffer[collected++] = (int16_t)s;
        }
    }
}

// ── EI signal callback ────────────────────────────────────────────────────────
static int get_signal_data(size_t offset, size_t length, float *out_ptr) {
    numpy::int16_to_float(inference_buffer + offset, out_ptr, length);
    return 0;
}

// ── LED indication ────────────────────────────────────────────────────────────
static void led_indicate(bool is_unknown) {
    if (is_unknown) {
        // Unknown: 5 rapid flashes
        for (int i = 0; i < 5; i++) {
            digitalWrite(LED_PIN, HIGH);
            delay(80);
            digitalWrite(LED_PIN, LOW);
            delay(80);
        }
    } else {
        // Enrolled: solid 1 second
        digitalWrite(LED_PIN, HIGH);
        delay(1000);
        digitalWrite(LED_PIN, LOW);
    }
}

// ── Setup ─────────────────────────────────────────────────────────────────────
void setup() {
    Serial.begin(115200);
    while (!Serial);

    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    i2s_init();

    Serial.println("{\"status\":\"ready\"}");
}

// ── Main loop ─────────────────────────────────────────────────────────────────
void loop() {
    unsigned long t_start = millis();

    // 1. Record audio
    record_audio();
    unsigned long t_capture = millis() - t_start;

    // 2. Run inference
    signal_t signal;
    signal.total_length = EI_CLASSIFIER_RAW_SAMPLE_COUNT;
    signal.get_data     = &get_signal_data;

    ei_impulse_result_t result = {0};
    unsigned long t_inf_start = millis();
    EI_IMPULSE_ERROR err = run_classifier(&signal, &result, false);
    unsigned long t_inference = millis() - t_inf_start;

    if (err != EI_IMPULSE_OK) {
        Serial.printf("{\"error\":%d}\n", err);
        return;
    }

    // 3. Find highest confidence prediction
    int   best_idx = 0;
    float best_val = 0.0f;
    for (int i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
        if (result.classification[i].value > best_val) {
            best_val = result.classification[i].value;
            best_idx = i;
        }
    }

    const char *predicted = result.classification[best_idx].label;

    // 4. Determine Unknown: model predicted N, OR confidence below threshold
    bool is_unknown = (strcmp(predicted, "N") == 0) || (best_val < CONFIDENCE_THRESHOLD);
    const char *output_label = is_unknown ? "Unknown" : predicted;

    // 5. LED indication
    led_indicate(is_unknown);

    unsigned long t_total = millis() - t_start;

    // 6. Structured JSON log (machine-readable)
    Serial.printf(
        "{\"label\":\"%s\",\"raw_label\":\"%s\",\"confidence\":%.3f,"
        "\"capture_ms\":%lu,\"inference_ms\":%lu,\"total_ms\":%lu}\n",
        output_label, predicted, best_val,
        t_capture, t_inference, t_total
    );

    // 7. Battery-aware: idle between inferences
    // Light sleep reduces current draw while keeping I2S and timer alive.
    // For deeper savings, replace with esp_deep_sleep_start() + timer wakeup.
    delay(SLEEP_MS);
}

#include <driver/i2s.h>

#define I2S_SCK      D1
#define I2S_WS       D2
#define I2S_SD       D0
#define LED_PIN      D3

#define SAMPLE_RATE  16000
#define RECORD_SECS  2
#define NUM_SAMPLES  (SAMPLE_RATE * RECORD_SECS)  // 32000

static int16_t audio_buf[NUM_SAMPLES];

void setup() {
  Serial.begin(921600);
  while (!Serial);

  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, HIGH);  // off (active low)

  i2s_config_t cfg = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_32BIT,
    .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 512,
    .use_apll = false,
  };
  i2s_pin_config_t pins = {
    .bck_io_num   = I2S_SCK,
    .ws_io_num    = I2S_WS,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num  = I2S_SD,
  };
  i2s_driver_install(I2S_NUM_0, &cfg, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pins);

  Serial.println("READY");
}

void loop() {
  if (!Serial.available()) return;
  char cmd = Serial.read();
  if (cmd == 'h') {
    Serial.println("READY");
    return;
  }
  if (cmd == 'r') {
    digitalWrite(LED_PIN, LOW);   // LED on: recording

    int32_t tmp[256];
    int collected = 0;
    while (collected < NUM_SAMPLES) {
      size_t bytes_read;
      int want = min(256, NUM_SAMPLES - collected);
      i2s_read(I2S_NUM_0, tmp, want * sizeof(int32_t), &bytes_read, portMAX_DELAY);
      int got = bytes_read / sizeof(int32_t);
      for (int i = 0; i < got; i++) {
        int32_t raw = (int32_t)(tmp[i] >> 16) * 8;
        if (raw > 32767)  raw = 32767;
        if (raw < -32768) raw = -32768;
        audio_buf[collected++] = (int16_t)raw;
      }
    }

    digitalWrite(LED_PIN, HIGH);  // LED off: done

    Serial.println("START");
    Serial.write((uint8_t*)audio_buf, NUM_SAMPLES * sizeof(int16_t));
    Serial.println("END");
  }
}

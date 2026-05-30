import serial
import json
import os
import csv
import glob
import subprocess
import time

PORT = '/dev/cu.usbmodem101'
BAUD = 115200
AUDIO_DIR = './peer_data/data'
OUTPUT_CSV = './model_stealing/victim_responses.csv'

os.makedirs('./model_stealing', exist_ok=True)

def play_audio(filepath):
    subprocess.Popen(['afplay', filepath])

def collect_response(ser, timeout=8):
    ser.reset_input_buffer()
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return None

def main():
    # 收集所有 WAV 文件
    wav_files = sorted(glob.glob(os.path.join(AUDIO_DIR, '**', '*.wav'), recursive=True))
    print(f"找到 {len(wav_files)} 个 WAV 文件")

    ser = serial.Serial(PORT, BAUD, timeout=10)
    time.sleep(2)  # 等串口稳定

    results = []
    for i, wav_path in enumerate(wav_files):
        filename = os.path.relpath(wav_path, AUDIO_DIR)
        speaker = wav_path.split(os.sep)[-3]  # e.g. S1

        print(f"[{i+1}/{len(wav_files)}] 播放 {filename} ...")

        # 播放音频
        play_audio(wav_path)

        # 收集 ESP32 输出
        response = collect_response(ser)

        if response:
            row = {
                'filename': filename,
                'true_label': speaker,
                'pred_label': response['label'],
                'confidence': response['confidence'],
                'raw_label': response['raw_label'],
            }
            results.append(row)
            print(f"  → {response['label']} (confidence: {response['confidence']:.3f})")
        else:
            print(f"  → 超时，跳过")
            results.append({
                'filename': filename,
                'true_label': speaker,
                'pred_label': 'TIMEOUT',
                'confidence': 0.0,
                'raw_label': 'TIMEOUT',
            })

        time.sleep(1)  # 等待下一次推理开始

    ser.close()

    # 保存 CSV
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'true_label', 'pred_label', 'confidence', 'raw_label'])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n完成！{len(results)} 条结果保存到 {OUTPUT_CSV}")

if __name__ == '__main__':
    main()

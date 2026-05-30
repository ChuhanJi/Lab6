import serial
import json
import os
from datetime import datetime

PORT = '/dev/cu.usbmodem101'
BAUD = 115200
OUTPUT_FILE = './logs/eval_logs.jsonl'

os.makedirs('./logs', exist_ok=True)

def collect(speaker_id, num_trials):
    ser = serial.Serial(PORT, BAUD, timeout=15)
    print(f"开始收集 {speaker_id} 的数据，共 {num_trials} 次")
    print("说 'AI runs on edge'，等 LED 反应后会自动记录...")

    collected = 0
    with open(OUTPUT_FILE, 'a') as f:
        while collected < num_trials:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line.startswith('{'):
                continue
            try:
                entry = json.loads(line)
                entry['ground_truth'] = speaker_id
                entry['timestamp'] = datetime.now().isoformat()
                f.write(json.dumps(entry) + '\n')
                collected += 1
                print(f"  [{collected}/{num_trials}] label={entry['label']} confidence={entry['confidence']:.3f}")
            except json.JSONDecodeError:
                continue

    ser.close()
    print(f"完成，保存到 {OUTPUT_FILE}")

if __name__ == '__main__':
    speaker = input("Ground truth speaker ID (e.g. S1 / Unknown): ").strip()
    trials = int(input("收集几条: "))
    collect(speaker, trials)

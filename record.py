import serial
import wave
import os

# 配置
PORT = '/dev/cu.usbmodem101'
BAUD = 921600
SAMPLE_RATE = 16000
RECORD_SECS = 2
TOTAL_BYTES = SAMPLE_RATE * RECORD_SECS * 2  # 16-bit = 2 bytes per sample
OUTPUT_DIR = './recordings'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def wait_ready(ser):
    ser.write(b'h')
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == 'READY':
            return

def record_session(ser, speaker_id, session_num):
    print(f"\n[{speaker_id} session{session_num:02d}] 准备好后按 Enter 开始录音（q 退出）...")
    user_input = input()
    if user_input.strip().lower() == 'q':
        return False

    wait_ready(ser)

    ser.write(b'r')

    # 等待 START（录音完成后才发）
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == 'START':
            break

    print("接收数据中...")

    raw_data = b''
    while len(raw_data) < TOTAL_BYTES:
        chunk = ser.read(TOTAL_BYTES - len(raw_data))
        if not chunk:
            print("错误：接收数据超时，请重试")
            return False
        raw_data += chunk

    print(f"录音完成，收到 {len(raw_data)} 字节")

    filename = f"{OUTPUT_DIR}/{speaker_id}_session{session_num:02d}.wav"
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(raw_data)

    print(f"保存到 {filename}")
    return True

if __name__ == '__main__':
    speaker = input("Speaker ID (e.g. S1): ").strip()
    start_session = int(input("从第几个 session 开始 (e.g. 1): "))

    ser = serial.Serial(PORT, BAUD, timeout=10)

    session = start_session
    while True:
        ok = record_session(ser, speaker, session)
        if not ok:
            break
        session += 1

    ser.close()
    print("录音结束。")

import json
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay

LOG_FILE = './logs/eval_logs.jsonl'

def load_logs():
    entries = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def main():
    entries = load_logs()
    if not entries:
        print("日志文件为空")
        return

    # normalize: ground_truth "N" and predicted "Unknown" both mean Unknown
    y_true = ['Unknown' if e['ground_truth'] == 'N' else e['ground_truth'] for e in entries]
    y_pred = [e['label'] for e in entries]
    confidences = [e['confidence'] for e in entries]
    inference_times = [e['inference_ms'] for e in entries]

    labels = sorted(set(y_true + y_pred))

    # 1. Classification report
    print("=== Classification Report ===")
    print(classification_report(y_true, y_pred, labels=labels, zero_division=0))

    # 2. Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    fig, ax = plt.subplots(figsize=(8, 6))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    disp.plot(ax=ax, cmap='Blues', colorbar=False)
    ax.set_title('Confusion Matrix')
    plt.tight_layout()
    plt.savefig('./logs/confusion_matrix.png', dpi=150)
    plt.show()
    print("混淆矩阵保存到 logs/confusion_matrix.png")

    # 3. Confidence distribution
    fig, ax = plt.subplots(figsize=(8, 4))
    correct = [c for c, t, p in zip(confidences, y_true, y_pred) if t == p]
    wrong   = [c for c, t, p in zip(confidences, y_true, y_pred) if t != p]
    ax.hist(correct, bins=20, alpha=0.6, label='Correct', color='green')
    ax.hist(wrong,   bins=20, alpha=0.6, label='Wrong',   color='red')
    ax.axvline(0.6, color='black', linestyle='--', label='Threshold (0.6)')
    ax.set_xlabel('Confidence')
    ax.set_ylabel('Count')
    ax.set_title('Confidence Distribution')
    ax.legend()
    plt.tight_layout()
    plt.savefig('./logs/confidence_distribution.png', dpi=150)
    plt.show()
    print("置信度分布保存到 logs/confidence_distribution.png")

    # 4. Timing stats
    print(f"\n=== Timing (ms) ===")
    print(f"Inference time — mean: {np.mean(inference_times):.1f}, std: {np.std(inference_times):.1f}")

if __name__ == '__main__':
    main()

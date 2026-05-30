import os
import csv
import numpy as np
import librosa
import joblib
from sklearn.svm import SVC
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

CSV_FILE = './victim_responses.csv'
AUDIO_BASE = '../peer_data/data'
MODEL_OUT = './surrogate_model.pkl'
ENCODER_OUT = './label_encoder.pkl'

def extract_mfcc(filepath, n_mfcc=13, sr=16000):
    y, _ = librosa.load(filepath, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])

def main():
    # 读取 CSV，过滤 TIMEOUT
    rows = []
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['pred_label'] != 'TIMEOUT':
                rows.append(row)

    print(f"有效查询数: {len(rows)}")

    # 提取特征，使用 pred_label 作为目标（不是 true_label）
    X, y = [], []
    for row in rows:
        audio_path = os.path.join(AUDIO_BASE, row['filename'])
        try:
            features = extract_mfcc(audio_path)
            X.append(features)
            y.append(row['pred_label'])
        except Exception as e:
            print(f"跳过 {row['filename']}: {e}")

    X = np.array(X)
    y = np.array(y)

    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    print(f"Labels: {le.classes_}")
    print(f"特征维度: {X.shape}")

    # 测量不同 query budget 下的 agreement rate
    budgets = [20, 50, len(rows)]
    print("\n=== Agreement Rate vs Query Budget ===")
    for budget in budgets:
        if budget > len(rows):
            continue
        X_train = X[:budget]
        y_train = y_enc[:budget]

        clf = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True)
        clf.fit(X_train, y_train)

        # agreement rate on held-out (remaining samples)
        if budget < len(rows):
            X_test = X[budget:]
            y_test = y_enc[budget:]
            y_pred = clf.predict(X_test)
            agreement = accuracy_score(y_test, y_pred)
        else:
            # 全部用于训练时，用训练集自身
            y_pred = clf.predict(X_train)
            agreement = accuracy_score(y_train, y_pred)

        print(f"  Budget={budget}: agreement rate = {agreement:.3f}")

    # 用全部数据训练最终模型
    clf_final = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True)
    clf_final.fit(X, y_enc)

    joblib.dump(clf_final, MODEL_OUT)
    joblib.dump(le, ENCODER_OUT)
    print(f"\n最终 surrogate 模型保存到 {MODEL_OUT}")

if __name__ == '__main__':
    main()

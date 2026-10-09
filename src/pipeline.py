"""Reusable SMS spam text pipeline: load, train, choose cost-based threshold, explain."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "SMSSpamCollection"
MODEL_PATH = ROOT / "models" / "spam_model.joblib"
C_FP, C_FN = 10, 1  # blocking a legitimate message costs 10x a missed spam
WARN_THRESHOLD = 0.50  # deliver with a warning between this and the block threshold (notebook section 13)


def load_data():
    df = pd.read_csv(DATA_PATH, sep="\t", header=None, names=["label", "message"], quoting=3)
    df = df.drop_duplicates(subset="message").reset_index(drop=True)
    return df["message"], (df["label"] == "spam").astype(int)


def build_pipeline(C=1.0):
    return Pipeline([
        ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2)),
        ("clf", CalibratedClassifierCV(LinearSVC(C=C, class_weight="balanced"), cv=3)),
    ])


def choose_threshold(y, p, c_fp=C_FP, c_fn=C_FN):
    best = None
    for t in np.round(np.arange(0.05, 0.99, 0.01), 2):
        pred = (p >= t).astype(int)
        fp = int(((pred == 1) & (y == 0)).sum())
        fn = int(((pred == 0) & (y == 1)).sum())
        key = (c_fp * fp + c_fn * fn, fp)
        if best is None or key < best[0]:
            best = (key, float(t))
    return best[1]


def explain(model, text):
    """Word-occlusion explanation: how much P(spam) drops when each word is removed."""
    words = text.split()
    base = float(model.predict_proba([text])[0, 1])
    if len(words) < 2:
        return base, words, [0.0] * len(words)
    variants = [" ".join(words[:i] + words[i + 1:]) for i in range(len(words))]
    contrib = (base - model.predict_proba(variants)[:, 1]).tolist()
    return base, words, contrib


def train_and_save():
    X, y = load_data()
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.4, stratify=y, random_state=42)
    X_val, _, y_val, _ = train_test_split(X_tmp, y_tmp, test_size=0.5, stratify=y_tmp, random_state=42)
    model = build_pipeline().fit(X_tr, y_tr)
    t = choose_threshold(y_val.to_numpy(), model.predict_proba(X_val)[:, 1])
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model, "threshold": t, "name": "LinearSVM + char"}, MODEL_PATH)
    print(f"Saved {MODEL_PATH} with threshold {t:.2f}")


if __name__ == "__main__":
    train_and_save()

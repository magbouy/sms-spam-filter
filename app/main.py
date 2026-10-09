from pathlib import Path
import joblib
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.pipeline import MODEL_PATH, WARN_THRESHOLD, explain

bundle = joblib.load(MODEL_PATH)
MODEL, THRESHOLD, NAME = bundle["model"], bundle["threshold"], bundle["name"]
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="SMS Spam Filter", version="1.0",
              description="Scores an SMS, returns spam probability and influential words. "
                          "Message text is processed in memory and never stored.")


class Message(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


@app.post("/predict")
def predict(msg: Message):
    p, words, contrib = explain(MODEL, msg.text)
    if p >= THRESHOLD:
        label, action = "spam", "move to spam folder (user can restore)"
    elif p >= WARN_THRESHOLD:
        label, action = "suspicious", "deliver with a warning"
    else:
        label, action = "ham", "deliver to inbox"
    tokens = [{"word": w, "contribution": round(c, 4)} for w, c in zip(words, contrib)]
    top = sorted(tokens, key=lambda t: abs(t["contribution"]), reverse=True)[:5]
    return {
        "spam_probability": round(p, 4),
        "threshold": THRESHOLD,
        "warn_threshold": WARN_THRESHOLD,
        "label": label,
        "action": action,
        "model": NAME,
        "top_features": top,
        "tokens": tokens,
    }


@app.get("/health")
def health():
    return {"status": "ok", "model": NAME, "threshold": THRESHOLD, "warn_threshold": WARN_THRESHOLD}


@app.get("/")
def home():
    return FileResponse(STATIC / "index.html")

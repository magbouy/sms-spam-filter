# SMS Spam Filter

An explainable SMS spam filter trained on the
[UCI SMS Spam Collection](https://archive.ics.uci.edu/dataset/228/sms+spam+collection).
It is a calibrated LinearSVM on character 2–5-gram TF-IDF features.

## Project contents

| Path | Purpose |
|---|---|
| `notebook.ipynb` | Data audit, model comparison, threshold analysis, calibration, explanations, robustness tests |
| `src/pipeline.py` | Reusable text pipeline: load, train, cost-based threshold, word-occlusion explanations |
| `app/main.py`, `app/static/index.html` | FastAPI service and web page |
| `models/spam_model.joblib` | Trained deployment model and its threshold |
| `responsible_use.md` | Responsible-use note |
| `Dockerfile` | Container used for deployment on Render |

## Service

- **Web page** (`/`): paste a message to see its spam probability and the words that
  influenced the decision.
- **REST API** (`POST /predict`, interactive docs at `/docs`): returns the probability,
  the label, the action and word-level contributions.

Decisions:
- **Spam (P ≥ 0.74):** moved to the spam folder, and the user can restore it.
- **Possibly suspicious (0.50 ≤ P < 0.74):** delivered with a warning.
- **Not spam (P < 0.50):** delivered.

The 0.74 threshold minimises cost on validation data when blocking a legitimate message
costs 10× a missed spam. Message text is processed in memory and never stored.

## Run locally

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m src.pipeline              # retrain the model from data/ (prints threshold 0.74)
uvicorn app.main:app --reload       # http://127.0.0.1:8000
```

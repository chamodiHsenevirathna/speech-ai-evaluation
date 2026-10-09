# Backend extract

A **reduced extract** of the SpeakLab FastAPI backend, kept here because the experiments
evaluate this code. It is not a runnable server: the API layer, middleware and upload
validation are not included.

| Path | Purpose |
|---|---|
| `app/services/metrics/` | Deterministic speech metrics: word count, WPM, long pauses (word-timestamp gaps), fillers (context-sensitive rules) |
| `app/services/transcription/` | The transcription interface and the local `faster-whisper` implementation (lazy-loaded) |
| `app/config.py` | Model name, device and compute-type defaults (`base.en`, `cpu`, `int8`) |
| `tests/` | Unit tests for the metrics and the transcription service (the model is mocked; no model is loaded or downloaded) |

## Python version

Use **Python 3.12** (3.11–3.13 should work). **Not 3.14**: `faster-whisper`'s dependency
chain (`av`, `onnxruntime`) had no compatible prebuilt wheels there on the machine used
for this work (Apple Silicon macOS). Only 3.12 was tested.

## Setup and tests

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest
```

The experiment READMEs activate this environment with `source ../../backend/.venv/bin/activate`.
The first transcription run in an experiment downloads the configured Whisper model (about
74 MB for `tiny.en`, 141 MB for `base.en`) and caches it under `~/.cache/huggingface/hub/`.

**Dependency note.** `av` is pinned below 19: with `av` 19 and `faster-whisper` 1.2.1 a real
transcription fails (`open() got an unexpected keyword argument 'metadata_errors'`), while the
unit tests still pass because they mock the model. A clean install with this pin (Python
3.12.14, `faster-whisper` 1.2.1, `av` 18.1.0) was tested; see the repository README.

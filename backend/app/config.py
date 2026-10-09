"""Local-development configuration constants.

CORS/upload-size are not env-driven - this backend only runs locally for V1 (see
docs/decision-log.md DEC-007). CORS origins are a small explicit allowlist, never a
wildcard (see docs/context.md's local-development CORS section).

Whisper model settings ARE env-driven (via .env / WHISPER_MODEL_SIZE etc.), with
defaults resolved by the M5 benchmark experiment - see docs/decision-log.md DEC-017 and
experiments/m5_transcription/.
"""

import os

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 25 MiB - a conservative safety margin for a browser recording of roughly one minute
# of speech. See docs/decision-log.md DEC-018 for the full rationale.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

# Resolved by the M5 local benchmark (see decision-log.md DEC-017 and
# experiments/m5_transcription/conclusions.md). Overridable via environment for
# experimentation without editing code.
WHISPER_MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "base.en")
WHISPER_DEVICE = os.environ.get("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")

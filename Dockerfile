# Test-runner image: Python 3.11 + CPU-only torch + Chromium with its system libraries.
# Build:  docker build -t playwright-zr .
# Run:    docker run --rm playwright-zr                      (offline suites)
#         docker compose up --exit-code-from tests           (with Ollama; see docker-compose.yml)
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    HF_HOME=/root/.cache/huggingface

WORKDIR /app

# Dependencies first so code edits don't invalidate this (slow) layer.
COPY requirements.txt .
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install -r requirements.txt \
 && python -m playwright install --with-deps chromium

COPY . .

# Default: everything that needs no LLM server. Override the command for other tiers.
CMD ["python", "-m", "pytest", "-m", "not live and not judge and not strong_judge and not mobile_native"]

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

# Metadata + packages first so code-only edits in tests/docs invalidate less.
COPY pyproject.toml README.md LICENSE ./
COPY ai ./ai
COPY api ./api
COPY apps ./apps
COPY config ./config
COPY data ./data
COPY db ./db
COPY mobile ./mobile
COPY pages ./pages
COPY reporting ./reporting
COPY visual ./visual

RUN pip install -U pip setuptools wheel \
 && pip install torch --index-url https://download.pytorch.org/whl/cpu \
 && pip install -e ".[core,apps,visual,mobile,ai]" \
 && python -m playwright install --with-deps chromium

COPY . .

# Default: everything that needs no LLM server. Override the command for other tiers.
CMD ["python", "-m", "pytest", "-m", "not live and not judge and not strong_judge and not mobile_native"]

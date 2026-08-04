# ---- Base image -------------------------------------------------------
FROM python:3.11-slim AS base

# Keeps Python from generating .pyc files and enables unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# ---- Dependencies ----------------------------------------------------
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ---- Application code ------------------------------------------------
COPY . .

# Create a non-root user and own the working directory
RUN addgroup --system appgroup && \
    adduser  --system --ingroup appgroup --no-create-home appuser && \
    mkdir -p reports && \
    chown -R appuser:appgroup /app

USER appuser

# Streamlit default port
EXPOSE 8501

# Health check so docker-compose / k8s knows when the app is ready
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')"

CMD ["streamlit", "run", "app.py", \
     "--server.address=0.0.0.0", \
     "--server.port=8501", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]

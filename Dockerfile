FROM python:3.12-slim
# idempotency_key: dockerfile-hardening-2025-10-24-v1
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8082
RUN useradd -m app && chown -R app:app /app
USER app
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8082"]

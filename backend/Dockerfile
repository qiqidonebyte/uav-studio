FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY frontend/public/models/uav/v1_1 /app/frontend/public/models/uav/v1_1
COPY frontend/public/training /app/frontend/public/training

RUN test -f /app/frontend/public/models/uav/v1_1/asset_manifest.json \
    && test -f /app/frontend/public/training/scenarios/index.json

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

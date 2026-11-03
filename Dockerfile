FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements-lock.txt .
RUN pip install --no-cache-dir -r requirements-lock.txt
COPY src src
COPY api api
COPY scripts scripts
COPY configs configs
COPY data/raw/financial_fraud_detection_dataset.csv data/raw/financial_fraud_detection_dataset.csv
# Train with the container's own dependency versions; never load cross-version local artifacts.
RUN python -m scripts.train && useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

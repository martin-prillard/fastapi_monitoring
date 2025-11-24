FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir build && \
    pip install --no-cache-dir . && \
    python train_model.py

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

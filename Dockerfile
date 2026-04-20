FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install fastapi uvicorn
RUN pip install fastapi uvicorn pandas rapidfuzz
RUN pip install -e .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
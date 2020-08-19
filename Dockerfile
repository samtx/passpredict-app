FROM python:3.8-slim

ENV PYTHONPATH=/app
ENV PYTHONBUFFERED=1

WORKDIR /app

COPY requirements.lock .

RUN pip install -r requirements.lock

COPY app .

EXPOSE 80
EXPOSE 8000

# CMD [ "gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker" ]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
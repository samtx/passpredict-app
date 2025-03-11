FROM python:3.12-slim

WORKDIR /worker

RUN pip install uv

COPY requirements.lock ./
RUN uv pip sync requirements.lock

COPY api ./

EXPOSE 8080

CMD ["python", "api/workflows/worker.py"]

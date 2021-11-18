FROM python:3.9-slim as builder

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
&& apt-get install --no-install-recommends -y gcc build-essential libpq-dev

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install wheel

# create and intall python wheels for dependencies
RUN pip wheel --wheel-dir=wheels -r requirements.txt


#########################################
FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install wheel

COPY --from=builder /app/wheels /app/wheels

# install python wheels for dependencies
RUN pip install --no-index --find-links=/app/wheels -r requirements.txt

# COPY ./setup.py setup.py
COPY ./app app

EXPOSE 8000

RUN chown 1000:1000 /app
USER 1000

CMD [ "gunicorn", "-b", "0.0.0.0:8010", "-w", "2", "app.main:app"]
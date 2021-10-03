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

# create python wheels for astrodynamics package
COPY astro_pkg/requirements.txt astro_pkg/requirements.txt
WORKDIR /app/astro_pkg
RUN pip install -r requirements.txt
RUN pip wheel --wheel-dir=/app/wheels -r requirements.txt
COPY astro_pkg/setup.py setup.py
COPY astro_pkg/astrodynamics astrodynamics
RUN python setup.py build_ext --inplace
RUN python setup.py bdist_wheel --dist-dir=/app/wheels


#########################################
FROM python:3.9-slim

WORKDIR /app

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE 1

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
COPY astro_pkg/requirements.txt requirements-astro.txt
RUN pip install wheel

COPY --from=builder /app/wheels /app/wheels

# install python wheels for dependencies
RUN pip install --no-index --find-links=/app/wheels -r requirements.txt
RUN pip install --no-index --find-links=/app/wheels -r requirements-astro.txt && pip uninstall cython -y
RUN pip install --no-index --find-links=/app/wheels astrodynamics

# COPY ./setup.py setup.py
COPY ./app app

EXPOSE 8000

RUN chown 1000:1000 /app
USER 1000

CMD [ "gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "-k", "app.workers.UvicornWorker", "--access-logfile=-", "app.main:app"]
# CMD ["uvicorn", "--proxy-headers", "--host", "0.0.0.0", "--port", "8000", "app.main:app"]
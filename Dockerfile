FROM node:15 as js-builder

# install dev dependencies
ENV NODE_ENV=development

WORKDIR /app

COPY package*.json .

RUN npm install

COPY rollup.config.js .
COPY app/static app/static

# build javascript and css bundles
RUN npm run build


###########################################
FROM python:3.9-slim as builder

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONBUFFERED=1
ENV SOFA_INSTALL_DIR=/usr/local/

RUN apt-get update \
&& apt-get install --no-install-recommends -y gcc build-essential

WORKDIR /app

# copy and build IAU SOFA static library
COPY cextern/sofa sofa
RUN cd sofa \
&& make \
&& make install \
&& make test \
&& cd .. \
&& rm -r sofa

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install wheel

# create and intall python wheels for dependencies
RUN pip wheel --wheel-dir=wheels -r requirements.txt
RUN pip install --no-index --find-links=wheels -r requirements.txt

# create python wheels for app
COPY setup.py .
COPY app app
RUN python setup.py build_ext --inplace
RUN python setup.py bdist_wheel --dist-dir=wheels


#########################################
FROM python:3.9-slim

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install wheel

COPY --from=builder /usr/local/include/*sofa* /usr/local/include/
COPY --from=builder /usr/local/lib/*sofa* /usr/local/lib/
COPY --from=builder /app/wheels /app/wheels

# install python wheels for dependencies
RUN pip install --no-index --find-links=/app/wheels -r requirements.txt

COPY ./setup.py setup.py
COPY ./app app
COPY ./tests tests
COPY ./pytest.ini pytest.ini

COPY --from=js-builder /app/app/static /app/app/static

EXPOSE 8000

RUN chown 1000:1000 /app
USER 1000

CMD [ "gunicorn", "-b", "0.0.0.0:8000", "-w", "3", "-k", "uvicorn.workers.UvicornWorker", "app.main:app"]
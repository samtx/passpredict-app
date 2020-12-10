FROM python:3.8-slim as builder

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

# # create python wheels for app
# COPY setup.py .
# COPY app app
# RUN python setup.py build_ext --inplace
# RUN pip wheel --wheel-dir=wheels .


# Multistage build
FROM python:3.8-slim

RUN apt-get update \
&& apt-get install --no-install-recommends -y gcc build-essential

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

COPY setup.py .
COPY app app
RUN python setup.py build_ext --inplace
RUN python setup.py install
COPY tests tests
COPY pytest.ini pytest.ini

EXPOSE 8000

# CMD [ "gunicorn", "app.main:app", "-b", "127.0.0.1:8000", "-w", "4", "-k", "uvicorn.workers.UvicornWorker" ]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
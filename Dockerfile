FROM python:3.8-slim

ENV PYTHONPATH=/app
ENV PYTHONBUFFERED=1

RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get install build-essential -y

WORKDIR /app

# copy and build IAU SOFA static library
COPY cextern/sofa sofa
RUN cd sofa \
&& make \
&& make install \
&& make test \
&& cd .. \
&& rm -r sofa

# && cd .. \
# && rm -r sofa

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY setup.py .
COPY app .
RUN python setup.py build_ext --inplace

EXPOSE 80
EXPOSE 8000

# CMD [ "gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker" ]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
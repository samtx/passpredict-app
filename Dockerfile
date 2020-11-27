FROM python:3.8-slim

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONBUFFERED=1
ENV SOFA_INSTALL_DIR=/usr/local/

RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get install build-essential -y \
&& apt-get install cron -y 

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
COPY app app
RUN python setup.py build_ext --inplace
RUN python setup.py install

EXPOSE 8000

# COPY crontab.txt .
# COPY ./docker-entrypoint.sh .
# RUN chmod +x docker-entrypoint.sh

# CMD [ "gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker" ]
# ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
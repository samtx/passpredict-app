FROM python:3.8-slim

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONBUFFERED=1

RUN apt-get update \
&& apt-get install -y cron

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

# create and intall python wheels for dependencies
RUN pip install sqlalchemy requests pydantic

# install python app without building extensions
COPY setup-cron.py .
COPY app app
RUN python setup-cron.py install

RUN touch /var/log/cron.log

RUN echo 'echo `date +"%c"` - TLEs should be updated' > /app/cron-output.sh && chmod +x /app/cron-output.sh

# Update TLE database every 8 hours
RUN echo "17 */8 * * * root /app/venv/bin/python /app/app/scripts/update_tle_database.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab 
RUN echo "17 */8 * * * root /app/cron-output.sh > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab 
# RUN echo "* * * * * root /app/cron-output.sh > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab 

# run cron in foreground
ENTRYPOINT ["cron", "-f"]
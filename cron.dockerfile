FROM python:3.8-slim

ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PYTHONBUFFERED=1

RUN apt-get update \
&& apt-get install -y cron

WORKDIR /app

# RUN python -m venv venv
# ENV PATH="/app/venv/bin:$PATH"

# create and intall python wheels for dependencies
RUN pip install sqlalchemy requests pydantic python-dotenv numpy

# install python app without building extensions
COPY setup-cron.py .
COPY app app
RUN python setup-cron.py install
RUN chmod +x app/scripts/cron-update-tle.sh

RUN touch /var/log/cron.log

RUN echo 'echo `date +"%c"` - TLEs should be updated' > /app/cron-output.sh && chmod +x /app/cron-output.sh

# Update TLE database every 8 hours
RUN echo "17 */8 * * * root bash /app/app/scripts/cron-update-tle.sh > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab \
    && echo "17 */8 * * * root cd /app && /app/cron-output.sh > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab
    # && echo "*/2 * * * * root bash /app/app/scripts/cron-update-tle.sh > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab 
    # && echo "* * * * * root cd /app/app/scripts/ && /usr/local/bin/python /app/app/scripts/update_tle_database.py > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab \
    # && echo "* * * * * root cd /app && /app/cron-output.sh > /proc/1/fd/1 2>/proc/1/fd/2" >> /etc/crontab 

# run cron in foreground
ENTRYPOINT ["cron", "-f"]
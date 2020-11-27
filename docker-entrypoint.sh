#!/bin/bash
set -e

# Start crontab
echo "set up cron jobs to update TLE database"
echo "schedule cron job"
cron crontab.txt

echo "Start Cron"
# service cron start
# touch /var/log/cron.log

echo "Start CMD"
# Hand off to CMD
exec "$@"

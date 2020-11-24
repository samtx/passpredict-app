#!/bin/bash
set -e

# Start crontab
echo "Start Cron"
service cron start
touch /var/log/cron.log

echo "Start CMD"
# Hand off to CMD
exec "$@"

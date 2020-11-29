# set environment variables in cron job before running update_tle_database.py script

echo "Set database environment variables"
export DATABASE_URI="sqlite:////db/passpredict.sqlite"
# printenv > /etc/environment

echo "Run update tle script"
/usr/local/bin/python /app/app/scripts/update_tle_database.py

echo "Generate static files"
. /home/sam/.nvm/nvm.sh
npm ci
npm run build

echo " Copy static files to serving directory "
cp -r --preserve=mode,ownership /opt/passpredict/app/static/* /var/www/passpredict.com/

echo " Verify files "
ls -lt /var/www/passpredict.com/
ls -lt /var/www/passpredict.com/dist
ls -lt /var/www/passpredict.com/css

exit 0
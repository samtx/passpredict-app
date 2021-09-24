set -ex

echo "Pull latest commit from Git repository"
git checkout main && git pull origin main

echo "Generate static files"
. /home/sam/.nvm/nvm.sh
. /home/sam/.bashrc
npm install
npm run build

echo " Copy static files to serving directory "
cp -r --preserve=mode,ownership /opt/passpredict/app/static/* /var/www/passpredict.com/

echo " Verify files "
ls -lt /var/www/passpredict.com/
ls -lt /var/www/passpredict.com/dist
ls -lt /var/www/passpredict.com/css

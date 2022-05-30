#!/bin/bash -e
#Build
cd /opt/star-burger/
git pull
source venv/bin/activate
pip install -r requirements.txt
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
python manage.py collectstatic --noinput
#Release
python manage.py migrate --noinput
systemctl restart star-burger.service
systemctl reload nginx.service
#Logging
REVISION=$(git rev-parse --short HEAD)
ROLLBAR_TOKEN=$(cat .env | grep ROLLBAR_TOKEN | cut -d "=" -f 2)
curl -H "Accept: application/json" -H "X-Rollbar-Access-Token: $ROLLBAR_TOKEN" -H "Content-Type: application/json" -X POST 'https://api.rollbar.com/api/1/deploy' -d '{"environment": "production", "revision": "'"$REVISION"'", "status": "succeeded"}'
echo "Deploy $REVISION is finished successfully"

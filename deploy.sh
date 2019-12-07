#!/bin/bash

set -e

SITE_PACKAGES=$(pipenv --venv)/lib/python3.7/site-packages
echo "Library Location: $SITE_PACKAGES"
DIR=$(pwd)

# Make sure pipenv is good to go
echo "Do fresh install to make sure everything is there"
pipenv install

cd $SITE_PACKAGES
zip -r9 $DIR/function.zip *

cd $DIR
zip -g function.zip main.py

echo "Deploy new version of lambda"
aws lambda update-function-code --function-name notifyNewChapters --zip-file fileb://function.zip

echo "Deploy successfully. Remove artifact"
rm function.zip

echo "Done"
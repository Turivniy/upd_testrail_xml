#! /bin/bash

set +ex

pip install virtualenv
virtualenv .venv
source .venv/bin/activate
pip install -r requirements.txt


export TESTRAIL_PLAN_NAME="" \
export TESTRAIL_URL="" \
export TESTRAIL_SUITE="" \
export TESTRAIL_PROJECT="" \
export TESTRAIL_MILESTONE="" \
export TESTRAIL_USER="" \
export TEST_GROUP="" \
export OUTPUT_XUNIT_REPORT="" \
export PASTE_BASE_URL="" \
export TESTRAIL_PASSWORD=""

python cmd.py \
    --testrail-plan-name "$TESTRAIL_PLAN_NAME" \
    --env-description "$TEST_GROUP" \
    --testrail-url  "$TESTRAIL_URL" \
    --testrail-user "$TESTRAIL_USER" \
    --testrail-password "$TESTRAIL_PASSWORD" \
    --testrail-project "$TESTRAIL_PROJECT" \
    --testrail-milestone "$TESTRAIL_MILESTONE" \
    --testrail-suite "$TESTRAIL_SUITE" \
    --output-xunit-report "$OUTPUT_XUNIT_REPORT" \
    --testrail-name-template '{title}' \
    --xunit-name-template '{classname}.{methodname}' verification.xml


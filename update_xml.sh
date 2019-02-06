#! /bin/bash

set +ex

echo "|=========================================================================================|"
echo "| Using update_xml.sh:                                                                    |"
echo "| $ . update_xml.sh [testrail username] [testrail password] [path to the xml report file] |"
echo "|=========================================================================================|"


TESTRAIL_USER=$1
TESTRAIL_PASSWORD=$2
REPORT=$3

if [ "$1" != "" ]; then
    echo "User has been set"
else
    echo "Provide testrail username"
fi

if [ "$2" != "" ]; then
    echo "Password has been set"
else
    echo "Provide testrail password"
fi

if [ "$3" != "" ]; then
    echo "Report file has been set"
else
    echo "Provide path to the xml report file"
fi

export TESTRAIL_PLAN_NAME="MCP1.1-OSCORE-2018-12-19" \
export TESTRAIL_URL="https://mirantis.testrail.com" \
export TESTRAIL_SUITE="[MCP1.1_PIKE]Tempest" \
export TESTRAIL_PROJECT="Mirantis Cloud Platform" \
export TESTRAIL_MILESTONE="MCP1.1" \
export TEST_GROUP="openstack" \
export OUTPUT_XUNIT_REPORT="output_verification.xml" \
export PASTE_BASE_URL="" \
export TESTRAIL_USER="sturivnyi@mirantis.com" \
export TESTRAIL_PASSWORD="Ssturivnyi123"

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
    --xunit-name-template '{classname}.{methodname}' $REPORT


TestRail xUnit Updater
======================

This updater helps to update *.xml report if test-suite or test-class has failed.

How to use
----------

Just update all the parameters in the update_xml.sh file

```
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
```

Run update_xml.sh script

``# . update_xml.sh``

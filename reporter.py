from __future__ import absolute_import, print_function

from functools import wraps
import logging
import re
import six

import xml.etree.ElementTree as ET

from client import Client as TrClient

logger = logging.getLogger(__name__)


def memoize(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        key = f.__name__
        cached = self._cache.get(key)
        if cached is None:
            cached = self._cache[key] = f(self, *args, **kwargs)
        return cached

    return wrapper


class Reporter(object):
    def __init__(self,
                 xunit_report,
                 output_xunit_report,
                 env_description,
                 test_results_link,
                 paste_url, *args, **kwargs):
        self._config = {}
        self._cache = {}
        self.xunit_report = xunit_report
        self.output_xunit_report = output_xunit_report
        self.env_description = env_description
        self.test_results_link = test_results_link
        self.paste_url = paste_url

        super(Reporter, self).__init__(*args, **kwargs)

    def config_testrail(self,
                        base_url,
                        username,
                        password,
                        project,
                        tests_suite,
                        send_skipped=False,
                        use_test_run_if_exists=False, send_duplicates=False):
        self._config['testrail'] = dict(base_url=base_url,
                                        username=username,
                                        password=password, )
        self.project_name = project
        self.tests_suite_name = tests_suite
        self.send_skipped = send_skipped
        self.send_duplicates = send_duplicates
        self.use_test_run_if_exists = use_test_run_if_exists

    @property
    def testrail_client(self):
        return TrClient(**self._config['testrail'])

    @property
    @memoize
    def project(self):
        return self.testrail_client.projects.find(name=self.project_name)

    @property
    @memoize
    def suite(self):
        return self.project.suites.find(name=self.tests_suite_name)

    @property
    @memoize
    def cases(self):
        return self.suite.cases()

# ================================================================

    def describe_testrail_case(self, case):
        return {
            k: v
            for k, v in case.data.items() if isinstance(v, six.string_types)
        }

    def get_cases(self):
        """Get all the testcases from the server"""
        cases_data = []
        cases = self.suite.cases()
        for case in cases:
            case_data = self.describe_testrail_case(case)
            cases_data.append(case_data)
        return cases_data

    def get_empty_classnames(self):
        tree = ET.parse(self.xunit_report)
        root = tree.getroot()

        classnames = []
        classnames_data = {'classname': '', 'data': ''}
        for child in root:
            if child.attrib['classname'] == '' and child[0].tag == 'failure':

                m = re.search('\(.*\)', child.attrib['name'])
                classname = m.group()[1:-1]

                classnames_data['classname'] = classname
                classnames_data['data'] = child[0].text

                classnames.append(classnames_data)

        return classnames

    def get_testcases(self, all_cases, empty_classnames):

        all_empty_cases = []
        all_data_empty_cases = {'classname': '', 'name': '', 'data': ''}
        for empty_classname in empty_classnames:
            for case in all_cases:
                if empty_classname['classname'] in case['title']:

                    all_data_empty_cases['classname'] = empty_classname['classname']
                    all_data_empty_cases['name'] = case['custom_report_label']
                    all_data_empty_cases['data'] = empty_classname['data']

                    all_empty_cases.append(all_data_empty_cases)

        # Remove duplicates and return list of dics
        return [dict(t) for t in {tuple(d.items()) for d in all_empty_cases}]

    def update_testcases(self, cases):

        tree = ET.parse(self.xunit_report)
        root = tree.getroot()

        for case in cases:
            testcase = ET.Element("testcase")
            testcase.attrib['classname'] = "{}".format(case['classname'])
            testcase.attrib['name'] = "{}".format(case['name'])
            testcase.attrib['time'] = "0.000"

            skip = ET.SubElement(testcase, 'failure')
            skip.text = case['data']

            root.append(testcase)

        tree = ET.ElementTree(root)
        tree.write(self.output_xunit_report)

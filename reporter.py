from __future__ import absolute_import, print_function

from functools import wraps
import logging
import os
import re
import six

import xml.etree.ElementTree as ET

from client import Client as TrClient

import logging
logging.basicConfig(level=logging.INFO)
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

    temporary_filename = 'temporary_xunit_report.xml'
    logger.info(' Temporrary filename is: {}'.format(temporary_filename))

    def describe_testrail_case(self, case):
        return {
            k: v
            for k, v in case.data.items() if isinstance(v, six.string_types)
        }

    def get_cases(self):
        """Get all the testcases from the server"""
        logger.info(' Start gerring cases from the Testrail')
        cases_data = []
        cases = self.suite.cases()
        for case in cases:
            case_data = self.describe_testrail_case(case)
            cases_data.append(case_data)
        logger.info(' Cases were got from the Testrail')
        return cases_data

    def get_empty_classnames(self):
        tree = ET.parse(self.xunit_report)
        root = tree.getroot()
        
        if root[0].tag == 'testsuite':
            root = root[0]

        classnames = []
        for child in root:
            if child.attrib['classname'] == '' and child[0].tag == 'failure':
                m = re.search('\(.*\)', child.attrib['name'])
                classname = m.group()[1:-1]
                classnames.append({'classname': classname, 'data': child[0].text})

        logger.info(' Got empty classnames from xml file')
        return classnames

    def get_testcases(self, all_cases, empty_classnames):
        needed_cases = []
        for empty_classname in empty_classnames:
            for case in all_cases:
                if empty_classname['classname'] in case['title']:

                    updated_case = {'classname': empty_classname['classname'],
                                    'name': case['custom_test_case_description'],
                                    'data': empty_classname['data']}
                    needed_cases.append(updated_case)
        logger.info(' Got test cases for updating xml file')
        return needed_cases

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

        for _ in cases:
            for child in root:
                try:
                    if child.attrib['classname'] == "":
                        child.clear()
                except KeyError:
                    pass
        logger.info(' Create temporrary file: {}'.format(str(self.temporary_filename)))
        tree = ET.ElementTree(root)
        tree.write(self.temporary_filename)
        logger.info(' Temporrary file was created: {}'.format(self.check_file_exists(self.temporary_filename)))

    def delete_duplicates(self):
        logger.info(' Start deleting duplicates from xml file: {}'.format(self.temporary_filename))
        tree = ET.parse(self.temporary_filename)
        root = tree.getroot()

        all_cases = []
        for child in root:
            try:
                all_cases.append((child.attrib['classname'], child.attrib['name']))
            except KeyError:
                pass
        # Get duplicates
        for_stack = lambda all_cases: sorted(list(set([x for x in all_cases if all_cases.count(x) > 1])))
        duplicate_cases = for_stack(all_cases)

        # Remove duplicates from xml
        for case in duplicate_cases:
            for child in root:
                try:
                    if child.attrib['classname'] == case[0] and child.attrib['name'] == case[1]:
                        if child.attrib['time'] == '0.000':
                            child.clear()
                except KeyError:
                    pass

        logger.info(' Start saving results to the file: {}'.format(self.output_xunit_report))
        tree = ET.ElementTree(root)
        tree.write(self.output_xunit_report)

        logger.info(' {} file was created: {}'.format(self.output_xunit_report, self.check_file_exists(self.output_xunit_report)))

    def check_file_exists(self, filename):
        return str(os.path.isfile(filename))

    def delete_temporary_file(self):
        os.remove(self.temporary_filename)
        logger.info(' Temporrary file exists: {}'.format(self.check_file_exists(self.temporary_filename)))

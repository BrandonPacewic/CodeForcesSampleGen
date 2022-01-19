#!/usr/bin/python3

from urllib.request import urlopen
from html.parser import HTMLParser

from subprocess import call
from functools import partial, wraps
from typing import Any, List, Tuple

import re
import argparse
import platform


TEMPLATE = 'template.cc'
LANUGAGE = 'C++17'
SAMPLE_INPUT = 'input'
SAMPLE_OUTPUT = 'output'
MY_OUTPUT = 'my_output'


VERSION = 'CodeForces Parser v1.5.1: Modified by Brandon'
RED_F = '\033[31m'
GREEN_F = '\033[32m'
BOLD = '\033[1m'
NORM = '\033[0m'


class codeforces_problem_parser(HTMLParser):
    def __init__(self, folder):
        HTMLParser.__init__(self)
        self.folder = folder
        self.num_tests = 0
        self.testcase = None
        self.start_copy = False

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            if attrs == [('class', 'input')]:
                self.num_tests += 1
                self.testcase = open(
                    '%s/%s%d' % (self.folder, SAMPLE_INPUT, self.num_tests), 'wb')
            elif attrs == [('class', 'output')]:
                self.testcase = open(
                    '%s/%s%d' % (self.folder, SAMPLE_OUTPUT, self.num_tests), 'wb')
        elif tag == 'pre':
            if self.testcase != None:
                self.start_copy = True

    def handle_endtag(self, tag):
        if tag == 'br':
            if self.start_copy:
                self.testcase.write('\n'.encode('utf-8'))
                self.end_line = True
        if tag == 'pre':
            if self.start_copy:
                if not self.end_line:
                    self.testcase.write('\n'.encode('utf-8'))
                self.testcase.close()
                self.testcase = None
                self.start_copy = False

    def handle_entityref(self, name):
        if self.start_copy:
            self.testcase.write(self.unescape(('&%s;' % name)).encode('utf-8'))

    def handle_data(self, data):
        if self.start_copy:
            self.testcase.write(data.strip('\n').encode('utf-8'))
            self.end_line = False


class codeforces_contest_parser(HTMLParser):
    def __init__(self, contest):
        HTMLParser.__init__(self)
        self.contest = contest
        self.start_contest = False
        self.start_problem = False
        self.name = ''
        self.problem_name = ''
        self.problems = []
        self.problem_names = []

    def handle_starttag(self, tag, attrs):
        if self.name == '' and attrs == [('style', 'color: black'), ('href', f'/contest/{self.contest}')]:
                self.start_contest = True
        elif tag == 'option':
            if len(attrs) == 1:
                regexp = re.compile(r"'[A-Z][0-9]?'") # The attrs will be something like: ('value', 'X'), or ('value', 'X1')
                string = str(attrs[0])
                search = regexp.search(string)
                if search is not None:
                    self.problems.append(search.group(0).split("'")[-2])
                    self.start_problem = True

    def handle_endtag(self, tag):
        if tag == 'a' and self.start_contest:
            self.start_contest = False
        elif self.start_problem:
            self.problem_names.append(self.problem_name)
            self.problem_name = ''
            self.start_problem = False

    def handle_data(self, data):
        if self.start_contest:
            self.name = data
        elif self.start_problem:
            self.problem_name += data



def parse_problem(folder: str, contest: str, problem: str) -> int:
    url = f'http://codeforces.com/contest/{contest}/problem/{problem}'
    html = urlopen(url).read()
    parser = codeforces_problem_parser(folder)
    parser.feed(html.decode('utf-8'))
    return parser.num_tests



def parse_contest_page(contest: str) -> Any:
    url = f'http://codeforces.com/contest/{contest}'
    html = urlopen(url).read()
    parser = codeforces_contest_parser(contest)
    parser.feed(html.decode('utf-8'))
    return parser


def main():
    def _output_info(contest: str, language: str, problems: List[str]) -> None:
        print(VERSION)
        print(f'Parsing contest {contest} for language {language}, please wait...')
        print(f'Found {len(problems)} problems')

    parser = argparse.ArgumentParser()
    parser.add_argument('contest', help='Contest# (Not round#)')
    args = parser.parse_args()

    contest = args.contest
    content = parse_contest_page(contest)

    _output_info(contest, LANGUAGE, content.problems)

    for index, problem in enumerate(content.problems):
        print ('Downloading Problem %s: %s...' % (problem, content.problem_names[index]))
        folder = '%s-%s/%s/' % (contest, LANGUAGE, problem)
        call(['mkdir', '-p', folder])
        call(['cp', '-n', TEMPLATE, '%s/%s.%s' % (folder, problem, TEMPLATE.split('.')[1])])
        num_tests = parse_problem(folder, contest, problem)
        print(f'{num_tests} sample test(s) found.')


if __name__ == '__main__':
    main()

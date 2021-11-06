#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
script_name.py
Description of script_name.py.
"""
import logging
import json
import shutil
import string
import random
from unittest import TestCase
from pathlib import Path
from ocd import DEFAULT_RULES
import app as ocd


class TestRules(TestCase):
    def setUp(self) -> None:
        # self.rules_path = Path(__file__).parent / 'rules_example.json'
        self.rules_path = Path(__file__).parent / 'rules_test.json'
        self.rules = DEFAULT_RULES
        print(DEFAULT_RULES)
        with self.rules_path.open('w') as f:
            json.dump(self.rules, f)

    def tearDown(self) -> None:
        if self.rules_path.is_file():
            self.rules_path.unlink()

    def test_init_rules(self):
        # TODO: Test for incomplete rules
        # Delete rules file
        self.rules_path.unlink()

        self.assertFalse(self.rules_path.is_file())
        # Run init
        result = ocd.init_rules(self.rules_path)

        # Check if rules.json exists
        self.assertTrue(self.rules_path.is_file())

        # Check if rules contain default rules
        with self.rules_path.open('r') as read_file:
            data = json.load(read_file)

        self.assertEqual(DEFAULT_RULES, data)

    def test_set_rules(self):
        self.fail()

    def test_get_rules_path(self):
        """Should return a Path object of given path or default if empty"""
        result = ocd.get_rules_path(self.rules_path)
        self.assertEqual(self.rules_path, result)

        result = ocd.get_rules_path()
        self.assertEqual(self.rules_path.parent / 'rules.json', result)

    def test_write_rules(self):
        rules = {'characters': {'jens': 'mens'}}
        result = ocd._write_rules(self.rules_path, rules)
        with self.rules_path.open('r') as read_file:
            data = json.load(read_file)

        self.assertEqual(data, rules)

    def test_load_rules(self):
        """Should in this case deliver the default rules"""
        result = ocd._load_rules(self.rules_path)
        self.assertEqual(DEFAULT_RULES, result)

    def test_get_rules(self):
        """Get rules from file"""
        rules = ocd.get_rules(rules_path=self.rules_path)
        self.assertIsInstance(rules, dict)

    def test_get_jobs(self):
        """Get jobs from rules"""
        jobs = ocd.get_jobs(self.rules)
        self.assertIsInstance(jobs, list)
        self.assertGreaterEqual(len(jobs), 1)
        self.assertIsInstance(jobs[0], dict)

    def test_get_groups(self):
        """Get groups from rules"""
        groups = ocd.get_groups(self.rules)
        self.assertIsInstance(groups, dict)
        self.assertGreaterEqual(len(groups.items()), 1)
        self.assertIsInstance(groups.get('document'), list)

    def test_get_extensions(self):
        """Get jobs from rules"""
        exts = ocd.get_extensions(self.rules)
        self.assertIsInstance(exts, dict)
        self.assertGreaterEqual(len([x for x in exts]), 1)
        self.assertEqual(exts['txt'], 'document')
        self.assertEqual(exts['txt'], 'document')

    def test_add_characters_to_rules(self):
        ocd.add_characters_to_rules(rules_path=self.rules_path, häst='hest')
        self.assertTrue(ocd._load_rules(self.rules_path))


class TestOperations(TestCase):
    def setUp(self) -> None:
        self.source = Path(__file__).parent / 'test_source'
        self.source.mkdir(parents=True, exist_ok=True)
        for d1 in string.ascii_letters[:16]:
            l = self.source / f'{d1}.txt'
            l.write_text(l.name)
            # Make a folder
            p1 = self.source / d1
            p1.mkdir(parents=True, exist_ok=True)

            # Make a file
            f1 = p1 / f'{p1.name}.txt'
            f1.write_text(d1)

            for d2 in string.ascii_letters[:8]:
                p2 = p1 / f'{d1}{d2}'
                p2.mkdir(parents=True, exist_ok=True)

                # Make a file
                f2 = p2 / f'{p2.name}.txt'
                f2.write_text(d2)

                for d3 in string.ascii_letters[:4]:
                    p3 = p2 / f'{d1}{d2}{d3}'
                    p3.mkdir(parents=True, exist_ok=True)

                    # Make a file
                    f3 = p3 / f'{p3.name}.txt'
                    f3.write_text(d3)

    def tearDown(self) -> None:
        shutil.rmtree(self.source)

    def test_copy(self):
        self.fail()

    def test_get_paths(self):
        files = ocd.get_paths(self.source)
        source = [x for x in self.source.iterdir()]
        self.assertEqual(len(source), len(files))
        self.assertEqual(sorted(source), sorted(files))

        # Test for subdirs
        files = ocd.get_paths(self.source, subdirs=True)
        self.assertNotEqual(len(source), len(files))
        self.assertNotEqual(sorted(source), sorted(files))
        source = [x for x in self.source.rglob('*')]
        self.assertEqual(len(source), len(files))
        self.assertEqual(sorted(source), sorted(files))

        # Test for custom pattern
        files = ocd.get_paths(self.source, pattern='a.txt')

        source = [self.source / 'a.txt']
        self.assertEqual(len(source), len(files))
        self.assertEqual(source, files)

        # Test for subdirs and custom pattern
        files = ocd.get_paths(self.source, pattern='a.txt', subdirs=True)
        self.assertNotEqual(len(source), len(files))
        self.assertNotEqual(sorted(source), sorted(files))
        source.append(self.source / 'a' / 'a.txt')
        self.assertEqual(len(source), len(files))
        self.assertEqual(sorted(source), sorted(files))


class TestHelpers(TestCase):
    def setUp(self) -> None:
        self.test_path = Path(__file__).parent / '_test_folder'
        self.test_path.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.test_path)

    def test_get_checksum(self):
        file_a = self.test_path / 'file_a'
        file_a.write_text('a')

        file_b = self.test_path / 'file_b'
        file_b.write_text('b')

        file_c = self.test_path / 'file_c'
        file_c.write_text('a')

        self.assertEqual(ocd.get_checksum(file_a), ocd.get_checksum(file_a))
        self.assertEqual(ocd.get_checksum(file_a), ocd.get_checksum(file_c))
        self.assertNotEqual(ocd.get_checksum(file_a), ocd.get_checksum(file_b))

    def test_verify_checksums(self):
        file_a = self.test_path / 'file_a'
        file_a.write_text('a')

        file_b = self.test_path / 'file_b'
        file_b.write_text('b')

        file_c = self.test_path / 'file_c'
        file_c.write_text('a')

        self.assertTrue(ocd.verify_checksums(file_a, file_a))
        self.assertTrue(ocd.verify_checksums(file_a, file_c))
        self.assertFalse(ocd.verify_checksums(file_a, file_b))

    def test_remove_characters(self):
        illegal_name = r'>" (greater than):'
        legal_name = ' (greater than)'
        result = ocd.remove_characters(illegal_name)
        self.assertEqual(result, legal_name)

    def test_replace_characters(self):
        illegal_name = r'> ¨(ëegreaterå than):'
        legal_name = '>_(eegreatera_than):'
        result = ocd.replace_characters(illegal_name)
        self.assertEqual(result, legal_name)

    def test_clean_string(self):
        illegal_name = r'> ¨(ëegreaterå than):'
        legal_name = '_(eegreatera_than)'
        result = ocd.clean_string(illegal_name)
        self.assertEqual(result, legal_name)

    def test_group_from_path(self):
        path = Path('test.txt')
        result = ocd.group_from_path(path)
        self.assertEqual('document', result)

    def test_generate_string(self):
        result = ocd.generate_string(10)
        self.assertEqual(10, len(result))
        for i in result:
            self.assertTrue(i in string.ascii_letters)


class TestJobs(TestCase):
    def test_run_jobs(self):
        ocd.run_jobs()
        self.fail()

    def test_run_job(self):
        ocd.run_job()
        self.fail()

    def test_get_job_attributes(self):
        test_job = dict(DEFAULT_RULES.get('jobs', [])[0])
        logging.debug(test_job)
        test_job['source'] = Path()
        test_job['destination'] = Path()
        job = ocd.get_job_attributes(test_job)

        self.assertIsNotNone(job.get('name'))
        self.assertIsNotNone(job.get('source'))
        self.assertIsNotNone(job.get('destination'))
        self.assertIsNotNone(job.get('operation'))
        self.assertIn(job.get('operation'), ocd.OPERATIONS)
        self.assertIsNotNone(job.get('target'))
        self.assertIn(job.get('target'), ocd.TARGETS)
        self.assertIsNotNone(job.get('subdirs'))
        self.assertIsNotNone(job.get('group'))
        self.assertIsNotNone(job.get('filename'))
        self.assertIsNotNone(job.get('verify'))
        self.assertIsNotNone(job.get('cleanup'))


    def test_files_paths(self):
        self.fail()

    def test_folders_paths(self):
        self.fail()

    def test_organize_files(self):
        self.fail()


class Test(TestCase):
    def test_organize_folders(self):
        self.fail()


class Test(TestCase):
    def test_job_prefix(self):
        self.fail()

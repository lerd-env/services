#!/usr/bin/env python3
"""Checks on the upstream image check, run in CI before it."""

import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_upstream_images import newer_versions, parse_tag  # noqa: E402


class ParseTagTest(unittest.TestCase):
    def test_splits_prefix_version_and_suffix(self):
        self.assertEqual(parse_tag("latest-pg17"), (("latest-pg", 1, ""), (17,)))
        self.assertEqual(parse_tag("3-management-alpine"), (("", 1, "-management-alpine"), (3,)))

    def test_tag_without_a_version_is_unchecked(self):
        self.assertIsNone(parse_tag("latest"))


class NewerVersionsTest(unittest.TestCase):
    def test_reports_a_new_major(self):
        self.assertEqual(newer_versions(["7"], ["6", "7", "8", "8.0"]), [("8", "8")])

    def test_quiet_when_pin_is_newest(self):
        self.assertEqual(newer_versions(["8"], ["7", "8"]), [])

    def test_compares_each_shape_against_its_own_newest_pin(self):
        found = newer_versions(["12.3", "11.8"], ["12.3", "12.4", "11.9"])
        self.assertEqual(found, [("12.4", "12.4")])

    def test_a_new_major_is_reported_once_across_shapes(self):
        found = newer_versions(["12", "12.3"], ["12", "12.3", "13", "13.0"])
        self.assertEqual(found, [("13", "13")])

    def test_a_pinned_major_already_follows_its_minors(self):
        self.assertEqual(newer_versions(["13", "12.3"], ["13", "12.3", "13.0", "13.1"]), [])

    def test_ignores_tags_of_another_shape(self):
        self.assertEqual(newer_versions(["pg18"], ["pg18", "pg19-trixie", "19beta1"]), [])

    def test_patch_releases_only_count_once_the_minor_moves(self):
        self.assertEqual(newer_versions(["2.19.5"], ["2.19.5", "2.19.6"]), [])
        self.assertEqual(newer_versions(["2.19.5"], ["2.19.6", "3.3.0", "3.3.1"]), [("3.3", "3.3.1")])

    def test_latest_pins_are_skipped(self):
        self.assertEqual(newer_versions(["latest"], ["latest", "9"]), [])


if __name__ == "__main__":
    unittest.main()

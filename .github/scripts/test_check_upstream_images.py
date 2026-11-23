#!/usr/bin/env python3
"""Checks on the upstream image check, run in CI before it."""

import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from check_upstream_images import ROOT, newer_versions, parse_tag, pinned_images  # noqa: E402


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

    def test_a_pin_lerd_updates_by_minor_stays_quiet_within_its_major(self):
        self.assertEqual(newer_versions(["2.2.0"], ["2.2.0", "2.5.0"], follows={"2.2.0"}), [])

    def test_a_pin_lerd_updates_by_minor_still_reports_a_new_major(self):
        found = newer_versions(["2.2.0"], ["2.5.0", "3.0.0"], follows={"2.2.0"})
        self.assertEqual(found, [("3.0", "3.0.0")])


class PinnedImagesTest(unittest.TestCase):
    def test_minor_update_strategy_marks_the_pins_it_follows(self):
        floci = pinned_images(ROOT)["docker.io/floci/floci"]
        self.assertEqual(floci["follows"], floci["tags"])

    def test_unwatched_repositories_are_left_out(self):
        self.assertNotIn("docker.io/localstack/localstack", pinned_images(ROOT))


if __name__ == "__main__":
    unittest.main()

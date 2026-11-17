#!/usr/bin/env python3
"""Checks on the schema guard's exemptions, run in CI beside it."""

import pathlib
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from schema_guard import removal_allowed  # noqa: E402


class RemovalAllowedTest(unittest.TestCase):
    def test_image_may_go_when_versions_take_over(self):
        self.assertTrue(removal_allowed("image", {"versions": {"list"}, "versions[].image": {"string"}}))

    def test_image_stays_without_versions(self):
        self.assertFalse(removal_allowed("image", {"name": {"string"}}))

    def test_other_keys_still_count(self):
        self.assertFalse(removal_allowed("ports", {"versions": {"list"}}))


if __name__ == "__main__":
    unittest.main()

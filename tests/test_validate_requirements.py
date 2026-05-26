from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import validate_requirements


class ValidateRequirementsTests(unittest.TestCase):
    def test_parse_env_prefers_dot_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.example").write_text("N8N_PORT=5678\n", encoding="utf-8")
            (root / ".env").write_text("N8N_PORT=7777\n", encoding="utf-8")

            self.assertEqual(validate_requirements.parse_env(root)["N8N_PORT"], "7777")

    def test_parse_env_uses_example_when_env_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env.example").write_text("N8N_PORT=5678\n", encoding="utf-8")

            self.assertEqual(validate_requirements.parse_env(root)["N8N_PORT"], "5678")

    def test_python_version_check_rejects_non_314(self) -> None:
        fake_version = SimpleNamespace(major=3, minor=12, micro=0)
        with mock.patch.object(validate_requirements.sys, "version_info", fake_version):
            passed, message = validate_requirements.check_python_version()

        self.assertFalse(passed)
        self.assertIn("Python 3.14 is required", message)


if __name__ == "__main__":
    unittest.main()

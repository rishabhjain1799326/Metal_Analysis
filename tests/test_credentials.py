import os
import unittest
from unittest.mock import patch

from app.credentials import get_credential


class CredentialTests(unittest.TestCase):
    def test_environment_variable_takes_priority_and_is_trimmed(self):
        with patch.dict(os.environ, {"TWELVE_DATA_API_KEY": "  test-key  "}):
            self.assertEqual(get_credential("TWELVE_DATA_API_KEY"), "test-key")


if __name__ == "__main__":
    unittest.main()

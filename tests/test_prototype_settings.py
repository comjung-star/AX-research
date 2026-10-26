import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from prototype.settings import load_local_env


class LocalSettingsTests(unittest.TestCase):
    def test_local_key_and_model_load_without_executing_file_content(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / ".env"
            path.write_text('OPENAI_API_KEY="sk-test-file-placeholder-123456"\nAX_LLM_MODEL=gpt-6-luna\nUNEXPECTED_SETTING=ignored\n', encoding="utf-8-sig")
            load_local_env(path)
            self.assertEqual(os.environ["OPENAI_API_KEY"], "sk-test-file-placeholder-123456")
            self.assertEqual(os.environ["AX_LLM_MODEL"], "gpt-6-luna")
            self.assertNotIn("UNEXPECTED_SETTING", os.environ)

    def test_existing_process_settings_take_precedence(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {"OPENAI_API_KEY": "existing-process-key"}, clear=True):
            path = Path(directory) / ".env"
            path.write_text("OPENAI_API_KEY=file-key\nAX_LLM_MODEL=\n", encoding="utf-8")
            load_local_env(path)
            self.assertEqual(os.environ["OPENAI_API_KEY"], "existing-process-key")
            self.assertNotIn("AX_LLM_MODEL", os.environ)

    def test_missing_file_and_blank_values_do_not_register_a_key(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            path = Path(directory) / ".env"
            load_local_env(path)
            path.write_text("# local settings\nOPENAI_API_KEY=\n", encoding="utf-8")
            load_local_env(path)
            self.assertNotIn("OPENAI_API_KEY", os.environ)


if __name__ == "__main__":
    unittest.main()

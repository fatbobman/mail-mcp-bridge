import importlib
import sys
import tempfile
import unittest
from email.message import EmailMessage
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cleanup_attachments import cleanup_attachments
from extract_attachments import extract_attachments
from attachment_paths import get_message_dir


class AttachmentPathSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.base_dir = self.root / "mail-mcp-attachments"
        self.base_dir.mkdir()
        self.victim_dir = self.root / "victim-dir"
        self.victim_dir.mkdir()
        (self.victim_dir / "evidence.txt").write_text("sentinel\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def create_emlx_with_attachment(self, filename="test.bin", payload=b"payload"):
        message = EmailMessage()
        message["Subject"] = "test"
        message["From"] = "a@example.com"
        message["To"] = "b@example.com"
        message.set_content("hello")
        message.add_attachment(
            payload,
            maintype="application",
            subtype="octet-stream",
            filename=filename,
        )

        emlx_path = self.root / "sample.emlx"
        emlx_path.write_bytes(b"0\n" + message.as_bytes())
        return emlx_path

    def test_cleanup_safely_handles_parent_traversal_shape(self):
        result = cleanup_attachments(["../victim-dir"], base_dir=str(self.base_dir))

        self.assertTrue(result["success"])
        self.assertEqual(result["cleaned"], [])
        self.assertEqual(result["not_found"], ["../victim-dir"])
        self.assertEqual(result["invalid"], [])
        self.assertTrue(self.victim_dir.exists())
        self.assertTrue((self.victim_dir / "evidence.txt").exists())

    def test_cleanup_safely_handles_absolute_path_shape(self):
        result = cleanup_attachments([str(self.victim_dir)], base_dir=str(self.base_dir))

        self.assertTrue(result["success"])
        self.assertEqual(result["not_found"], [str(self.victim_dir)])
        self.assertEqual(result["invalid"], [])
        self.assertTrue(self.victim_dir.exists())

    def test_cleanup_safely_handles_backslash_path_shape(self):
        result = cleanup_attachments(["..\\victim-dir"], base_dir=str(self.base_dir))

        self.assertTrue(result["success"])
        self.assertEqual(result["invalid"], [])
        self.assertTrue(self.victim_dir.exists())
        self.assertEqual(result["not_found"], ["..\\victim-dir"])

    def test_cleanup_rejects_symlink_escape(self):
        symlink_path = get_message_dir(self.base_dir, "linked-message")
        symlink_path.symlink_to(self.victim_dir, target_is_directory=True)

        result = cleanup_attachments(["linked-message"], base_dir=str(self.base_dir))

        self.assertTrue(result["success"])
        self.assertEqual(len(result["invalid"]), 1)
        self.assertTrue(self.victim_dir.exists())

    def test_cleanup_removes_valid_directory(self):
        message_dir = get_message_dir(self.base_dir, "msg@example.com")
        message_dir.mkdir()
        (message_dir / "attachment.txt").write_text("data\n")

        result = cleanup_attachments(["msg@example.com"], base_dir=str(self.base_dir))

        self.assertTrue(result["success"])
        self.assertEqual(len(result["cleaned"]), 1)
        self.assertFalse(message_dir.exists())
        self.assertEqual(result["invalid"], [])

    def test_extract_safely_handles_parent_traversal_shape(self):
        emlx_path = self.create_emlx_with_attachment()

        result = extract_attachments(
            str(emlx_path),
            "../victim-dir",
            ["test.bin"],
            output_dir=str(self.base_dir),
        )

        self.assertTrue(result["success"])
        message_dir = Path(result["message_dir"])
        self.assertEqual(message_dir.parent, self.base_dir.resolve())
        self.assertTrue((message_dir / "test.bin").exists())
        self.assertFalse((self.victim_dir / "test.bin").exists())

    def test_extract_rejects_symlink_escape(self):
        emlx_path = self.create_emlx_with_attachment()
        symlink_path = get_message_dir(self.base_dir, "linked-message")
        symlink_path.symlink_to(self.victim_dir, target_is_directory=True)

        result = extract_attachments(
            str(emlx_path),
            "linked-message",
            ["test.bin"],
            output_dir=str(self.base_dir),
        )

        self.assertFalse(result["success"])
        self.assertFalse((self.victim_dir / "test.bin").exists())

    def test_extract_writes_to_valid_directory(self):
        emlx_path = self.create_emlx_with_attachment()

        result = extract_attachments(
            str(emlx_path),
            "msg@example.com",
            ["test.bin"],
            output_dir=str(self.base_dir),
        )

        self.assertTrue(result["success"])
        message_dir = Path(result["message_dir"])
        self.assertEqual(message_dir.parent, self.base_dir.resolve())
        self.assertTrue((message_dir / "test.bin").exists())
        self.assertEqual(result["not_found"], [])

    def test_slash_message_id_is_encoded_and_supported(self):
        emlx_path = self.create_emlx_with_attachment()

        extract_result = extract_attachments(
            str(emlx_path),
            "<abc/123@example.com>",
            ["test.bin"],
            output_dir=str(self.base_dir),
        )

        self.assertTrue(extract_result["success"])
        message_dir = Path(extract_result["message_dir"])
        self.assertEqual(message_dir.parent, self.base_dir.resolve())
        self.assertNotIn("/", message_dir.name)
        self.assertTrue((message_dir / "test.bin").exists())

        cleanup_result = cleanup_attachments(
            ["<abc/123@example.com>"],
            base_dir=str(self.base_dir),
        )

        self.assertTrue(cleanup_result["success"])
        self.assertEqual(len(cleanup_result["cleaned"]), 1)
        self.assertFalse(message_dir.exists())
        self.assertEqual(cleanup_result["invalid"], [])

    def test_package_imports_work(self):
        cleanup_module = importlib.import_module("src.cleanup_attachments")
        extract_module = importlib.import_module("src.extract_attachments")

        self.assertTrue(callable(cleanup_module.cleanup_attachments))
        self.assertTrue(callable(extract_module.extract_attachments))


if __name__ == "__main__":
    unittest.main()

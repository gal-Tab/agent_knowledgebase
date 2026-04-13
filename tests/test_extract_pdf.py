"""Tests for PDF extraction (tools/extract-pdf.py)."""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
EXTRACT_SCRIPT = PROJECT_ROOT / "tools" / "extract-pdf.py"


class TestExtractPdfCLI:
    def test_no_args_prints_usage(self):
        result = subprocess.run(
            [sys.executable, str(EXTRACT_SCRIPT)],
            capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "Usage" in result.stderr

    def test_missing_file_fails(self):
        result = subprocess.run(
            [sys.executable, str(EXTRACT_SCRIPT), "/nonexistent/file.pdf"],
            capture_output=True, text=True
        )
        assert result.returncode == 1
        assert "Error" in result.stderr


class TestExtractPdfFunction:
    def test_main_with_mocked_pymupdf(self, tmp_path):
        """Test extract-pdf.py with a mocked pymupdf4llm module."""
        # Create a fake PDF file (content doesn't matter since we mock)
        fake_pdf = tmp_path / "test.pdf"
        fake_pdf.write_text("fake pdf content")

        output_file = tmp_path / "output.md"

        # Mock pymupdf4llm
        mock_module = MagicMock()
        mock_module.to_markdown.return_value = "# Extracted Content\n\nThis is the extracted text."

        with patch.dict(sys.modules, {"pymupdf4llm": mock_module}):
            with patch("sys.argv", ["extract-pdf.py", str(fake_pdf), str(output_file)]):
                # Import and run main
                import importlib.util
                spec = importlib.util.spec_from_file_location("extract_pdf", EXTRACT_SCRIPT)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.main()

        assert output_file.exists()
        content = output_file.read_text()
        assert "Extracted Content" in content
        mock_module.to_markdown.assert_called_once_with(str(fake_pdf))

    def test_stdout_output_with_mocked_pymupdf(self, tmp_path, capsys):
        """Test extract-pdf.py outputs to stdout when no output file given."""
        fake_pdf = tmp_path / "test.pdf"
        fake_pdf.write_text("fake pdf")

        mock_module = MagicMock()
        mock_module.to_markdown.return_value = "# Stdout Output"

        with patch.dict(sys.modules, {"pymupdf4llm": mock_module}):
            with patch("sys.argv", ["extract-pdf.py", str(fake_pdf)]):
                import importlib.util
                spec = importlib.util.spec_from_file_location("extract_pdf_2", EXTRACT_SCRIPT)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                mod.main()

        captured = capsys.readouterr()
        assert "Stdout Output" in captured.out

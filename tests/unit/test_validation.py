import os
from unittest.mock import MagicMock, patch

from providers.ollama_client import validate_model_id as validate_ollama
from providers.openai_client import validate_model_id as validate_openai


class TestValidation:
    
    @patch("httpx.get")
    def test_validate_openai_success(self, mock_get):
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"id": "gpt-4o"}, {"id": "gpt-4o-mini"}]
        }
        mock_get.return_value = mock_response
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            assert validate_openai("gpt-4o") is True
            assert validate_openai("gpt-4o-mini") is True
            assert validate_openai("gpt-5-nonexistent") is False

    @patch("httpx.get")
    def test_validate_openai_no_key(self, mock_get):
        # Should return True (skip validation) if no key
        with patch.dict(os.environ, {}, clear=True):
            assert validate_openai("anything") is True
        
        mock_get.assert_not_called()

    @patch("subprocess.run")
    def test_validate_ollama_success(self, mock_run):
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NAME\tID\tSIZE\tMODIFIED\nllama3.1:8b\t1234\t4GB\tToday\ndeepseek-coder:6.7b\t5678\t4GB\tToday"
        mock_run.return_value = mock_result
        
        assert validate_ollama("llama3.1:8b") is True
        assert validate_ollama("deepseek-coder:6.7b") is True
        assert validate_ollama("nonexistent") is False

    @patch("subprocess.run")
    def test_validate_ollama_failure(self, mock_run):
        # Simulate ollama down
        mock_run.side_effect = Exception("Ollama not running")
        assert validate_ollama("llama3.1:8b") is False

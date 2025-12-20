"""
Comprehensive tests for embeddings service.
"""

import pytest
from unittest.mock import patch, MagicMock
import hashlib

from fbx_core.services.embeddings import compute_text_and_hash, embed_text


class TestComputeTextAndHash:
    """Test compute_text_and_hash function."""

    def test_combines_all_fields(self):
        """Test that all text fields are combined."""
        title = "Test Title"
        summary = "Test Summary"
        explanation = "Test Explanation"
        model_name = "test-model"

        combined, hash_value = compute_text_and_hash(title, summary, explanation, model_name)

        assert "Test Title" in combined
        assert "Test Summary" in combined
        assert "Test Explanation" in combined

    def test_separates_fields_with_newlines(self):
        """Test fields are separated with double newlines."""
        title = "Title"
        summary = "Summary"
        explanation = "Explanation"
        model_name = "model"

        combined, _ = compute_text_and_hash(title, summary, explanation, model_name)

        # Should have newline separators
        assert "\n\n" in combined

    def test_handles_empty_fields(self):
        """Test handling of empty fields."""
        title = "Title"
        summary = ""
        explanation = ""
        model_name = "model"

        combined, hash_value = compute_text_and_hash(title, summary, explanation, model_name)

        # Should only contain title (empty fields excluded)
        assert combined == "Title"

    def test_hash_is_sha256(self):
        """Test that hash is SHA256."""
        title = "Test"
        summary = ""
        explanation = ""
        model_name = "model"

        _, hash_value = compute_text_and_hash(title, summary, explanation, model_name)

        # SHA256 produces 64 character hex string
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_hash_includes_model_name(self):
        """Test that hash includes model name."""
        title = "Test"
        summary = ""
        explanation = ""

        _, hash1 = compute_text_and_hash(title, summary, explanation, "model-1")
        _, hash2 = compute_text_and_hash(title, summary, explanation, "model-2")

        # Different models should produce different hashes
        assert hash1 != hash2

    def test_hash_is_deterministic(self):
        """Test that same input produces same hash."""
        title = "Test Title"
        summary = "Test Summary"
        explanation = "Test Explanation"
        model_name = "model"

        _, hash1 = compute_text_and_hash(title, summary, explanation, model_name)
        _, hash2 = compute_text_and_hash(title, summary, explanation, model_name)

        assert hash1 == hash2

    def test_different_content_produces_different_hash(self):
        """Test that different content produces different hashes."""
        model_name = "model"

        _, hash1 = compute_text_and_hash("Title 1", "", "", model_name)
        _, hash2 = compute_text_and_hash("Title 2", "", "", model_name)

        assert hash1 != hash2

    def test_combined_text_order(self):
        """Test order of combined text fields."""
        title = "Title"
        summary = "Summary"
        explanation = "Explanation"
        model_name = "model"

        combined, _ = compute_text_and_hash(title, summary, explanation, model_name)

        # Title should come first, then summary, then explanation
        title_pos = combined.find("Title")
        summary_pos = combined.find("Summary")
        explanation_pos = combined.find("Explanation")

        assert title_pos < summary_pos < explanation_pos

    def test_handles_special_characters(self):
        """Test handling of special characters."""
        title = "Title with 'quotes' and \"double quotes\""
        summary = "Summary with\nnewlines"
        explanation = "Explanation with émojis 🎉"
        model_name = "model"

        combined, hash_value = compute_text_and_hash(title, summary, explanation, model_name)

        assert "quotes" in combined
        assert "newlines" in combined
        assert "🎉" in combined
        assert len(hash_value) == 64

    def test_handles_unicode(self):
        """Test handling of unicode characters."""
        title = "Título en español"
        summary = "中文摘要"
        explanation = "Объяснение на русском"
        model_name = "model"

        combined, hash_value = compute_text_and_hash(title, summary, explanation, model_name)

        assert "español" in combined
        assert "中文" in combined
        assert "русском" in combined

    def test_returns_tuple(self):
        """Test that function returns a tuple."""
        result = compute_text_and_hash("Title", "", "", "model")

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_combined_text_is_string(self):
        """Test that combined text is a string."""
        combined, _ = compute_text_and_hash("Title", "Summary", "", "model")

        assert isinstance(combined, str)

    def test_hash_is_string(self):
        """Test that hash is a string."""
        _, hash_value = compute_text_and_hash("Title", "", "", "model")

        assert isinstance(hash_value, str)


class TestEmbedText:
    """Test embed_text function."""

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_returns_list(self, mock_transformer):
        """Test that embed_text returns a list."""
        # Mock the transformer
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        result = embed_text("Test text", "test-model")

        assert isinstance(result, list)
        assert len(result) == 3
        assert result == [0.1, 0.2, 0.3]

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_loads_model(self, mock_transformer):
        """Test that embed_text loads the specified model."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        embed_text("Test text", "sentence-transformers/all-MiniLM-L6-v2")

        mock_transformer.assert_called_once_with("sentence-transformers/all-MiniLM-L6-v2")

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_encodes_text(self, mock_transformer):
        """Test that embed_text encodes the input text."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        text = "This is test text"
        embed_text(text, "test-model")

        mock_model.encode.assert_called_once()
        call_args = mock_model.encode.call_args[0]
        assert text in call_args[0]

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_normalizes_embeddings(self, mock_transformer):
        """Test that embed_text normalizes embeddings."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        embed_text("Test text", "test-model")

        # Check normalize_embeddings=True was passed
        call_kwargs = mock_model.encode.call_args[1]
        assert call_kwargs.get("normalize_embeddings") is True

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_handles_numpy_array(self, mock_transformer):
        """Test that embed_text converts numpy array to list."""
        import numpy as np

        mock_model = MagicMock()
        # Return numpy array
        numpy_array = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = [numpy_array]
        mock_transformer.return_value = mock_model

        result = embed_text("Test text", "test-model")

        assert isinstance(result, list)
        assert result == [0.1, 0.2, 0.3]

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_handles_list(self, mock_transformer):
        """Test that embed_text handles already-list vectors."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        result = embed_text("Test text", "test-model")

        assert isinstance(result, list)

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_with_empty_string(self, mock_transformer):
        """Test embedding empty string."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.0] * 384]
        mock_transformer.return_value = mock_model

        result = embed_text("", "test-model")

        assert isinstance(result, list)
        assert len(result) == 384

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_with_long_text(self, mock_transformer):
        """Test embedding long text."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        long_text = "word " * 1000  # 1000 words
        result = embed_text(long_text, "test-model")

        assert isinstance(result, list)
        mock_model.encode.assert_called_once()

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_with_unicode(self, mock_transformer):
        """Test embedding text with unicode characters."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        unicode_text = "Hello 世界 🌍"
        result = embed_text(unicode_text, "test-model")

        assert isinstance(result, list)

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_different_models(self, mock_transformer):
        """Test embedding with different model names."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        # Test with different model names
        models = [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
            "custom-model",
        ]

        for model_name in models:
            embed_text("Test text", model_name)
            mock_transformer.assert_called_with(model_name)

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_returns_float_list(self, mock_transformer):
        """Test that embed_text returns list of floats."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_transformer.return_value = mock_model

        result = embed_text("Test text", "test-model")

        assert all(isinstance(x, float) for x in result)

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_embed_text_correct_dimensionality(self, mock_transformer):
        """Test that embed_text returns correct vector dimensionality."""
        mock_model = MagicMock()
        # all-MiniLM-L6-v2 produces 384-dimensional vectors
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        result = embed_text("Test text", "all-MiniLM-L6-v2")

        assert len(result) == 384


class TestEmbeddingsIntegration:
    """Integration tests for embeddings functionality."""

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_compute_and_embed_workflow(self, mock_transformer):
        """Test complete workflow of computing hash and embedding."""
        # Setup mock
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        # Step 1: Compute text and hash
        title = "Healthcare Reform Act"
        summary = "A bill to reform healthcare"
        explanation = "This bill aims to improve healthcare access"
        model_name = "test-model"

        combined, content_hash = compute_text_and_hash(title, summary, explanation, model_name)

        assert combined
        assert content_hash
        assert len(content_hash) == 64

        # Step 2: Generate embedding
        vector = embed_text(combined, model_name)

        assert vector
        assert len(vector) == 384
        assert all(isinstance(x, float) for x in vector)

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_same_content_produces_same_hash(self, mock_transformer):
        """Test that same content produces same hash for deduplication."""
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]
        mock_transformer.return_value = mock_model

        title = "Test Bill"
        summary = "Test Summary"
        explanation = "Test Explanation"
        model_name = "model"

        # Generate hash twice
        _, hash1 = compute_text_and_hash(title, summary, explanation, model_name)
        _, hash2 = compute_text_and_hash(title, summary, explanation, model_name)

        # Should be identical for deduplication
        assert hash1 == hash2

    @patch('fbx_core.services.embeddings.SentenceTransformer')
    def test_different_content_produces_different_embeddings(self, mock_transformer):
        """Test that different content would produce different embeddings."""
        mock_model = MagicMock()

        # Return different embeddings for different texts
        def encode_side_effect(texts, normalize_embeddings=True):
            if "Healthcare" in texts[0]:
                return [[0.1] * 384]
            else:
                return [[0.9] * 384]

        mock_model.encode.side_effect = encode_side_effect
        mock_transformer.return_value = mock_model

        # Embed two different texts
        vector1 = embed_text("Healthcare Reform Act", "model")
        vector2 = embed_text("Education Funding Bill", "model")

        # Vectors should be different
        assert vector1 != vector2

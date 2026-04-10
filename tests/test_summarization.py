"""
Unit tests for text summarization service.
Tests specific examples, edge cases, and core functionality.
"""

import pytest
from app.services.summarization import (
    TextSummarizer,
    SummaryParams,
    SummaryResult,
    SummaryLength,
    get_text_summarizer
)


class TestSummaryParams:
    """Test SummaryParams configuration class."""
    
    def test_default_params(self):
        """Test default parameter values."""
        params = SummaryParams()
        assert params.max_length == 150
        assert params.min_length == 40
        assert params.length_penalty == 2.0
        assert params.num_beams == 4
        assert params.early_stopping is True
    
    def test_custom_params(self):
        """Test custom parameter values."""
        params = SummaryParams(
            max_length=200,
            min_length=50,
            length_penalty=1.5,
            num_beams=6,
            early_stopping=False
        )
        assert params.max_length == 200
        assert params.min_length == 50
        assert params.length_penalty == 1.5
        assert params.num_beams == 6
        assert params.early_stopping is False
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        params = SummaryParams(max_length=100, min_length=30)
        params_dict = params.to_dict()
        assert params_dict["max_length"] == 100
        assert params_dict["min_length"] == 30
        assert "length_penalty" in params_dict
        assert "num_beams" in params_dict


class TestSummaryResult:
    """Test SummaryResult data class."""
    
    def test_summary_result_creation(self):
        """Test creating a SummaryResult."""
        params = SummaryParams()
        result = SummaryResult(
            summary_text="This is a summary.",
            original_length=500,
            summary_length=20,
            params=params,
            model_version="t5-base"
        )
        assert result.summary_text == "This is a summary."
        assert result.original_length == 500
        assert result.summary_length == 20
        assert result.model_version == "t5-base"
        assert result.generated_at is not None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        params = SummaryParams()
        result = SummaryResult(
            summary_text="Summary text",
            original_length=100,
            summary_length=15,
            params=params,
            model_version="t5-base"
        )
        result_dict = result.to_dict()
        assert result_dict["summary_text"] == "Summary text"
        assert result_dict["original_length"] == 100
        assert result_dict["summary_length"] == 15
        assert "params" in result_dict
        assert "generated_at" in result_dict


class TestTextSummarizer:
    """Test TextSummarizer service."""
    
    @pytest.fixture
    def summarizer(self):
        """Create a TextSummarizer instance for testing."""
        return TextSummarizer()
    
    def test_initialization(self, summarizer):
        """Test summarizer initialization."""
        assert summarizer.model_name == "t5-base"
        assert summarizer.device in ["cuda", "cpu"]
        assert summarizer._model is None  # Lazy loading
        assert summarizer._tokenizer is None
    
    def test_empty_input(self, summarizer):
        """Test summarization with empty input."""
        result = summarizer.generate_summary([])
        assert result.summary_text == ""
        assert result.original_length == 0
        assert result.summary_length == 0
    
    def test_empty_strings(self, summarizer):
        """Test summarization with empty strings."""
        result = summarizer.generate_summary(["", "  ", ""])
        assert result.summary_text == ""
        assert result.original_length == 0
    
    def test_single_text_summarization(self, summarizer):
        """Test summarization of a single text."""
        text = (
            "The Ministry of Corporate Affairs (MCA21) is seeking public consultation "
            "on proposed amendments to corporate governance regulations. The consultation "
            "period will run for 60 days and stakeholders are encouraged to submit their "
            "feedback through the official portal."
        )
        result = summarizer.generate_summary([text], max_length=50, min_length=10)
        
        assert isinstance(result, SummaryResult)
        assert len(result.summary_text) > 0
        assert result.original_length == len(text)
        assert result.summary_length == len(result.summary_text)
        assert result.model_version == "t5-base"
    
    def test_multiple_texts_summarization(self, summarizer):
        """Test summarization of multiple texts."""
        texts = [
            "The new regulations will improve corporate transparency.",
            "Stakeholders have expressed concerns about implementation timelines.",
            "The ministry is committed to addressing all feedback received."
        ]
        result = summarizer.generate_summary(texts, max_length=60, min_length=15)
        
        assert isinstance(result, SummaryResult)
        assert len(result.summary_text) > 0
        assert result.original_length > 0
        assert result.summary_length > 0
    
    def test_custom_summary_with_params(self, summarizer):
        """Test summarization with custom parameters."""
        texts = [
            "Corporate governance is essential for business integrity. "
            "The proposed amendments aim to strengthen accountability and transparency. "
            "Public consultation ensures diverse perspectives are considered."
        ]
        params = SummaryParams(
            max_length=80,
            min_length=20,
            length_penalty=1.5,
            num_beams=3
        )
        result = summarizer.generate_custom_summary(texts, params)
        
        assert isinstance(result, SummaryResult)
        assert len(result.summary_text) > 0
        assert result.params.max_length == 80
        assert result.params.min_length == 20
    
    def test_regenerate_summary(self, summarizer):
        """Test summary regeneration with different parameters."""
        texts = [
            "The consultation process is open to all stakeholders. "
            "Feedback will be reviewed by the regulatory committee."
        ]
        
        # Generate initial summary
        params1 = SummaryParams(max_length=50, min_length=10)
        result1 = summarizer.generate_custom_summary(texts, params1)
        
        # Regenerate with different parameters
        params2 = SummaryParams(max_length=100, min_length=20)
        result2 = summarizer.regenerate_summary(texts, params2)
        
        assert isinstance(result1, SummaryResult)
        assert isinstance(result2, SummaryResult)
        # Both should produce summaries (may or may not be different)
        assert len(result1.summary_text) > 0
        assert len(result2.summary_text) > 0
    
    def test_different_summary_lengths(self, summarizer):
        """Test generating summaries with different length constraints."""
        text = (
            "The Ministry of Corporate Affairs has announced new regulations "
            "for corporate governance. These regulations aim to improve transparency "
            "and accountability in corporate operations. Stakeholders have been given "
            "60 days to provide feedback on the proposed changes."
        )
        
        # Short summary
        result_short = summarizer.generate_summary([text], max_length=30, min_length=10)
        
        # Long summary
        result_long = summarizer.generate_summary([text], max_length=100, min_length=40)
        
        assert len(result_short.summary_text) > 0
        assert len(result_long.summary_text) > 0
        # Longer max_length should generally produce longer summaries
        # (though not guaranteed due to model behavior)
    
    def test_model_info(self, summarizer):
        """Test getting model information."""
        info = summarizer.get_model_info()
        assert info["model_name"] == "t5-base"
        assert info["device"] in ["cuda", "cpu"]
        assert "model_type" in info
    
    def test_long_text_truncation(self, summarizer):
        """Test that long texts are properly truncated."""
        # Create a very long text that exceeds model's max input length
        long_text = " ".join(["This is a sentence about corporate governance."] * 100)
        result = summarizer.generate_summary([long_text], max_length=50, min_length=10)
        
        assert isinstance(result, SummaryResult)
        assert len(result.summary_text) > 0


class TestGlobalSummarizerInstance:
    """Test the global summarizer instance getter."""
    
    def test_get_text_summarizer(self):
        """Test getting the global summarizer instance."""
        summarizer1 = get_text_summarizer()
        summarizer2 = get_text_summarizer()
        
        # Should return the same instance
        assert summarizer1 is summarizer2
        assert isinstance(summarizer1, TextSummarizer)


class TestSummaryLength:
    """Test SummaryLength preset class."""

    def test_short_preset(self):
        """Test short length preset values."""
        params = SummaryLength.get_params(SummaryLength.SHORT)
        assert params.max_length == 60
        assert params.min_length == 20

    def test_medium_preset(self):
        """Test medium length preset values."""
        params = SummaryLength.get_params(SummaryLength.MEDIUM)
        assert params.max_length == 150
        assert params.min_length == 40

    def test_long_preset(self):
        """Test long length preset values."""
        params = SummaryLength.get_params(SummaryLength.LONG)
        assert params.max_length == 300
        assert params.min_length == 80

    def test_unknown_preset_defaults_to_medium(self):
        """Test that an unknown preset falls back to medium."""
        params = SummaryLength.get_params("unknown")
        medium = SummaryLength.get_params(SummaryLength.MEDIUM)
        assert params.max_length == medium.max_length
        assert params.min_length == medium.min_length

    def test_preset_ordering(self):
        """Test that short < medium < long in terms of max_length."""
        short = SummaryLength.get_params(SummaryLength.SHORT)
        medium = SummaryLength.get_params(SummaryLength.MEDIUM)
        long = SummaryLength.get_params(SummaryLength.LONG)
        assert short.max_length < medium.max_length < long.max_length


class TestGenerateSummaryByLength:
    """Test generate_summary_by_length method."""

    @pytest.fixture
    def summarizer(self):
        return TextSummarizer()

    @pytest.fixture
    def sample_texts(self):
        return [
            "The Ministry of Corporate Affairs has proposed new regulations for corporate governance.",
            "Stakeholders are encouraged to submit feedback during the 60-day consultation period.",
            "The amendments aim to improve transparency and accountability in corporate operations.",
        ]

    def test_short_summary(self, summarizer, sample_texts):
        """Test generating a short summary."""
        result = summarizer.generate_summary_by_length(sample_texts, "short")
        assert isinstance(result, SummaryResult)
        assert len(result.summary_text) > 0
        assert result.params.max_length == 60

    def test_medium_summary(self, summarizer, sample_texts):
        """Test generating a medium summary."""
        result = summarizer.generate_summary_by_length(sample_texts, "medium")
        assert isinstance(result, SummaryResult)
        assert len(result.summary_text) > 0
        assert result.params.max_length == 150

    def test_long_summary(self, summarizer, sample_texts):
        """Test generating a long summary."""
        result = summarizer.generate_summary_by_length(sample_texts, "long")
        assert isinstance(result, SummaryResult)
        assert len(result.summary_text) > 0
        assert result.params.max_length == 300

    def test_default_length_is_medium(self, summarizer, sample_texts):
        """Test that default length preset is medium."""
        result = summarizer.generate_summary_by_length(sample_texts)
        assert result.params.max_length == 150

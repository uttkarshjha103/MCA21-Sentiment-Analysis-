"""
Unit tests for the data anonymization utility (Task 10.3).

Validates: Requirements 10.4
"""
import pytest
from app.utils.anonymizer import anonymize_text, anonymize_comment_dict, AnonymizationResult


# ---------------------------------------------------------------------------
# Email masking
# ---------------------------------------------------------------------------

class TestEmailMasking:
    def test_simple_email(self):
        result = anonymize_text("Contact me at user@example.com for details.")
        assert "[EMAIL]" in result.anonymized_text
        assert "user@example.com" not in result.anonymized_text
        assert result.pii_found.get("email") == 1

    def test_multiple_emails(self):
        result = anonymize_text("Send to a@b.com and c@d.org please.")
        assert result.pii_found.get("email") == 2

    def test_no_email(self):
        result = anonymize_text("No contact info here.")
        assert result.pii_found.get("email", 0) == 0
        assert result.anonymized_text == "No contact info here."

    def test_email_masking_disabled(self):
        result = anonymize_text("user@example.com", mask_email=False)
        assert "user@example.com" in result.anonymized_text
        assert result.pii_found.get("email", 0) == 0


# ---------------------------------------------------------------------------
# Phone masking
# ---------------------------------------------------------------------------

class TestPhoneMasking:
    def test_indian_mobile(self):
        result = anonymize_text("Call me on 9876543210.")
        assert "[PHONE]" in result.anonymized_text
        assert result.pii_found.get("phone", 0) >= 1

    def test_indian_mobile_with_prefix(self):
        result = anonymize_text("My number is +91 9876543210.")
        assert "[PHONE]" in result.anonymized_text

    def test_international_phone(self):
        result = anonymize_text("Reach me at +1-800-555-1234.")
        assert "[PHONE]" in result.anonymized_text

    def test_phone_masking_disabled(self):
        result = anonymize_text("9876543210", mask_phone=False)
        assert "9876543210" in result.anonymized_text


# ---------------------------------------------------------------------------
# Aadhaar masking
# ---------------------------------------------------------------------------

class TestAadhaarMasking:
    def test_aadhaar_plain(self):
        result = anonymize_text("My Aadhaar is 1234 5678 9012.")
        assert "[AADHAAR]" in result.anonymized_text
        assert result.pii_found.get("aadhaar", 0) >= 1

    def test_aadhaar_no_spaces(self):
        result = anonymize_text("Aadhaar: 123456789012")
        assert "[AADHAAR]" in result.anonymized_text

    def test_aadhaar_disabled(self):
        result = anonymize_text("123456789012", mask_aadhaar=False)
        assert "123456789012" in result.anonymized_text


# ---------------------------------------------------------------------------
# PAN masking
# ---------------------------------------------------------------------------

class TestPANMasking:
    def test_pan_card(self):
        result = anonymize_text("PAN: ABCDE1234F")
        assert "[PAN]" in result.anonymized_text
        assert result.pii_found.get("pan", 0) == 1

    def test_pan_disabled(self):
        result = anonymize_text("ABCDE1234F", mask_pan=False)
        assert "ABCDE1234F" in result.anonymized_text


# ---------------------------------------------------------------------------
# IP address masking
# ---------------------------------------------------------------------------

class TestIPMasking:
    def test_ipv4(self):
        result = anonymize_text("Request from 192.168.1.100.")
        assert "[IP_ADDRESS]" in result.anonymized_text
        assert result.pii_found.get("ip_address", 0) == 1

    def test_ip_disabled(self):
        result = anonymize_text("192.168.1.1", mask_ip=False)
        assert "192.168.1.1" in result.anonymized_text


# ---------------------------------------------------------------------------
# URL masking (opt-in)
# ---------------------------------------------------------------------------

class TestURLMasking:
    def test_url_disabled_by_default(self):
        result = anonymize_text("Visit https://example.com for info.")
        assert "https://example.com" in result.anonymized_text

    def test_url_enabled(self):
        result = anonymize_text("Visit https://example.com for info.", mask_url=True)
        assert "[URL]" in result.anonymized_text
        assert result.pii_found.get("url", 0) == 1


# ---------------------------------------------------------------------------
# Mixed PII
# ---------------------------------------------------------------------------

class TestMixedPII:
    def test_multiple_pii_types(self):
        text = "Email: test@example.com, Phone: 9876543210, IP: 10.0.0.1"
        result = anonymize_text(text)
        assert "[EMAIL]" in result.anonymized_text
        assert "[PHONE]" in result.anonymized_text
        assert "[IP_ADDRESS]" in result.anonymized_text
        assert result.has_pii is True
        assert result.total_replacements >= 3

    def test_empty_text(self):
        result = anonymize_text("")
        assert result.anonymized_text == ""
        assert result.has_pii is False

    def test_no_pii_text(self):
        result = anonymize_text("This is a clean comment about policy reform.")
        assert result.has_pii is False
        assert result.anonymized_text == "This is a clean comment about policy reform."


# ---------------------------------------------------------------------------
# anonymize_comment_dict
# ---------------------------------------------------------------------------

class TestAnonymizeCommentDict:
    def test_masks_comment_text_field(self):
        comment = {"comment_text": "Email me at foo@bar.com", "source": "web"}
        result = anonymize_comment_dict(comment)
        assert "[EMAIL]" in result["comment_text"]
        assert result["_anonymized"] is True
        assert result["_pii_found"].get("email") == 1
        # Original dict unchanged
        assert "foo@bar.com" in comment["comment_text"]

    def test_missing_field_returns_copy(self):
        comment = {"source": "web"}
        result = anonymize_comment_dict(comment)
        assert result == comment

    def test_custom_field(self):
        comment = {"body": "Call 9876543210", "id": 1}
        result = anonymize_comment_dict(comment, text_field="body")
        assert "[PHONE]" in result["body"]

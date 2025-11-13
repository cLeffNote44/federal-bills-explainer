"""
Comprehensive tests for CongressGovProvider.
"""

import pytest
import json
import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, Mock
import httpx

from fbx_core.providers.congress_gov import (
    CongressGovProvider,
    _iso,
    _get,
    _as_list,
)
from fbx_core.providers.base import BillRecord
from fbx_core.utils.rate_limiter import RateLimitConfig


class TestHelperFunctions:
    """Test helper functions."""

    def test_iso_with_timezone(self):
        """Test _iso with timezone-aware datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = _iso(dt)

        assert result == "2024-01-01T12:00:00Z"

    def test_iso_without_timezone(self):
        """Test _iso with naive datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = _iso(dt)

        assert result == "2024-01-01T12:00:00Z"

    def test_get_single_level(self):
        """Test _get with single level."""
        data = {"key": "value"}
        result = _get(data, "key")

        assert result == "value"

    def test_get_nested_levels(self):
        """Test _get with nested levels."""
        data = {"level1": {"level2": {"level3": "value"}}}
        result = _get(data, "level1", "level2", "level3")

        assert result == "value"

    def test_get_with_default(self):
        """Test _get with default value."""
        data = {"key": "value"}
        result = _get(data, "missing", default="default")

        assert result == "default"

    def test_get_with_none(self):
        """Test _get returns None for missing keys."""
        data = {"key": "value"}
        result = _get(data, "missing")

        assert result is None

    def test_as_list_with_none(self):
        """Test _as_list with None."""
        result = _as_list(None)

        assert result == []

    def test_as_list_with_list(self):
        """Test _as_list with list."""
        result = _as_list([1, 2, 3])

        assert result == [1, 2, 3]

    def test_as_list_with_single_value(self):
        """Test _as_list with single value."""
        result = _as_list("value")

        assert result == ["value"]


class TestCongressGovProviderInit:
    """Test CongressGovProvider initialization."""

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_init_with_defaults(self, mock_settings):
        """Test provider initialization with defaults."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        assert provider.name == "congress_gov"
        assert provider.api_key == "test-key"
        assert provider.fixtures_dir == "fixtures"

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_init_with_custom_fixtures_dir(self, mock_settings):
        """Test provider initialization with custom fixtures directory."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider(fixtures_dir="/custom/fixtures")

        assert provider.fixtures_dir == "/custom/fixtures"

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_init_with_custom_rate_limit(self, mock_settings):
        """Test provider initialization with custom rate limit config."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        custom_config = RateLimitConfig(
            requests_per_second=2.0,
            burst_size=10,
        )
        provider = CongressGovProvider(rate_limit_config=custom_config)

        assert provider.rate_limiter is not None


class TestCongressGovProviderFetchBills:
    """Test fetch_bills_updated_since method."""

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_fetch_bills_dry_run_mode(self, mock_settings, tmp_path):
        """Test fetch bills in dry-run mode uses fixtures."""
        mock_settings_instance = Mock()
        mock_settings_instance.dry_run = True
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        # Create fixture file
        fixtures_dir = tmp_path / "fixtures"
        fixtures_dir.mkdir()
        fixture_file = fixtures_dir / "congress_gov_became_law_sample.json"

        fixture_data = {
            "results": [
                {
                    "congress": 118,
                    "billType": "hr",
                    "billNumber": 1234,
                    "title": "Test Bill",
                }
            ]
        }
        fixture_file.write_text(json.dumps(fixture_data))

        provider = CongressGovProvider(fixtures_dir=str(fixtures_dir))
        bills = list(provider.fetch_bills_updated_since(None))

        assert len(bills) == 1
        assert bills[0]["congress"] == 118

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_fetch_bills_no_api_key(self, mock_settings, tmp_path):
        """Test fetch bills without API key uses fixtures."""
        mock_settings_instance = Mock()
        mock_settings_instance.dry_run = False
        mock_settings_instance.congress_api_key = None
        mock_settings.return_value = mock_settings_instance

        # Create fixture file
        fixtures_dir = tmp_path / "fixtures"
        fixtures_dir.mkdir()
        fixture_file = fixtures_dir / "congress_gov_became_law_sample.json"

        fixture_data = {
            "results": [
                {
                    "congress": 118,
                    "billType": "hr",
                    "billNumber": 5678,
                }
            ]
        }
        fixture_file.write_text(json.dumps(fixture_data))

        provider = CongressGovProvider(fixtures_dir=str(fixtures_dir))
        bills = list(provider.fetch_bills_updated_since(None))

        assert len(bills) == 1

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_fetch_bills_missing_fixture(self, mock_settings):
        """Test fetch bills with missing fixture file."""
        mock_settings_instance = Mock()
        mock_settings_instance.dry_run = True
        mock_settings_instance.congress_api_key = None
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider(fixtures_dir="/nonexistent")
        bills = list(provider.fetch_bills_updated_since(None))

        # Should return empty iterator
        assert len(bills) == 0

    @patch('fbx_core.providers.congress_gov.httpx.Client')
    @patch('fbx_core.providers.congress_gov.Settings')
    def test_fetch_bills_with_since_parameter(self, mock_settings, mock_client):
        """Test fetch bills with since parameter."""
        mock_settings_instance = Mock()
        mock_settings_instance.dry_run = False
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        # Mock HTTP client
        mock_response = Mock()
        mock_response.json.return_value = {
            "bills": [],
            "pagination": {}
        }
        mock_response.raise_for_status = Mock()
        mock_response.headers = {}

        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client.return_value = mock_client_instance

        provider = CongressGovProvider()
        since = datetime(2024, 1, 1, tzinfo=timezone.utc)

        with patch.object(provider.rate_limiter, 'execute', side_effect=lambda f: f()):
            list(provider.fetch_bills_updated_since(since))

        # Verify API was called with correct parameters
        assert mock_client_instance.get.called

    @patch('fbx_core.providers.congress_gov.httpx.Client')
    @patch('fbx_core.providers.congress_gov.Settings')
    def test_fetch_bills_pagination(self, mock_settings, mock_client):
        """Test fetch bills handles pagination."""
        mock_settings_instance = Mock()
        mock_settings_instance.dry_run = False
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        # Mock responses for pagination
        response1 = Mock()
        response1.json.return_value = {
            "bills": [
                {"congress": 118, "billType": "hr", "billNumber": 1}
            ],
            "pagination": {"next": "/bill?offset=100"}
        }
        response1.raise_for_status = Mock()
        response1.headers = {}

        response2 = Mock()
        response2.json.return_value = {
            "bills": [],
            "pagination": {}
        }
        response2.raise_for_status = Mock()
        response2.headers = {}

        response_detail = Mock()
        response_detail.json.return_value = {
            "bill": {
                "congress": 118,
                "billType": "hr",
                "billNumber": 1,
                "title": "Test Bill",
                "laws": [{"number": "118-1"}]
            }
        }
        response_detail.raise_for_status = Mock()
        response_detail.headers = {}

        mock_client_instance = MagicMock()
        mock_client_instance.get.side_effect = [response1, response_detail, response2]
        mock_client_instance.__enter__.return_value = mock_client_instance
        mock_client_instance.__exit__.return_value = None
        mock_client.return_value = mock_client_instance

        provider = CongressGovProvider()

        with patch.object(provider.rate_limiter, 'execute', side_effect=lambda f: f()):
            bills = list(provider.fetch_bills_updated_since(None))

        # Should have fetched bills from both pages
        assert len(bills) >= 1


class TestCongressGovProviderExtractIdentity:
    """Test _extract_identity method."""

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_extract_identity_simple(self, mock_settings):
        """Test extracting identity from simple bill data."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        item = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
        }

        result = provider._extract_identity(item)

        assert result is not None
        assert result["congress"] == 118
        assert result["bill_type"] == "hr"
        assert result["number"] == 1234

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_extract_identity_nested(self, mock_settings):
        """Test extracting identity from nested bill data."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        item = {
            "bill": {
                "congress": 118,
                "billType": "s",
                "billNumber": 5678,
            }
        }

        result = provider._extract_identity(item)

        assert result is not None
        assert result["congress"] == 118
        assert result["bill_type"] == "s"

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_extract_identity_invalid(self, mock_settings):
        """Test extracting identity from invalid data."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        item = {"invalid": "data"}

        result = provider._extract_identity(item)

        assert result is None

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_extract_identity_lowercase_type(self, mock_settings):
        """Test bill type is converted to lowercase."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        item = {
            "congress": 118,
            "billType": "HR",
            "billNumber": 1234,
        }

        result = provider._extract_identity(item)

        assert result["bill_type"] == "hr"


class TestCongressGovProviderNormalizeBill:
    """Test _normalize_bill method."""

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_simple(self, mock_settings):
        """Test normalizing simple bill data."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "title": "Test Bill Title",
        }

        result = provider._normalize_bill(bill_data)

        assert result["congress"] == 118
        assert result["bill_type"] == "hr"
        assert result["number"] == 1234
        assert result["title"] == "Test Bill Title"

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_titles_array(self, mock_settings):
        """Test normalizing bill with titles array."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "titles": [
                {"type": "short", "title": "Short Title"},
                {"type": "enacted", "title": "Enacted Title"},
            ]
        }

        result = provider._normalize_bill(bill_data)

        # Should prefer enacted title
        assert result["title"] == "Enacted Title"

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_summary(self, mock_settings):
        """Test normalizing bill with summary."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "summary": {"text": "Bill summary text"},
        }

        result = provider._normalize_bill(bill_data)

        assert result["summary"] == "Bill summary text"

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_public_law(self, mock_settings):
        """Test normalizing bill with public law number."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "laws": [{"number": "118-123"}]
        }

        result = provider._normalize_bill(bill_data)

        assert result["public_law_number"] == "118-123"

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_sponsor(self, mock_settings):
        """Test normalizing bill with sponsor."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "sponsors": [
                {"name": "Rep. Smith", "party": "D"}
            ]
        }

        result = provider._normalize_bill(bill_data)

        assert result["sponsor"] == {"name": "Rep. Smith", "party": "D"}

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_committees(self, mock_settings):
        """Test normalizing bill with committees."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "committees": [
                {"name": "Committee on Energy"},
                {"name": "Committee on Commerce"},
            ]
        }

        result = provider._normalize_bill(bill_data)

        assert result["committees"] == ["Committee on Energy", "Committee on Commerce"]

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_subjects(self, mock_settings):
        """Test normalizing bill with subjects."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "subjects": {
                "policyArea": {"name": "Energy"},
                "legislativeSubjects": [
                    {"name": "Alternative energy"},
                    {"name": "Climate change"},
                ]
            }
        }

        result = provider._normalize_bill(bill_data)

        assert "Energy" in result["subjects"]
        assert "Alternative energy" in result["subjects"]
        assert "Climate change" in result["subjects"]

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_cosponsors(self, mock_settings):
        """Test normalizing bill with cosponsors."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "cosponsors": [
                {"name": "Rep. Jones"},
                {"name": "Rep. Brown"},
                {"name": "Rep. Davis"},
            ]
        }

        result = provider._normalize_bill(bill_data)

        assert result["cosponsors_count"] == 3

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_normalize_bill_with_dates(self, mock_settings):
        """Test normalizing bill with dates."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()

        bill_data = {
            "congress": 118,
            "billType": "hr",
            "billNumber": 1234,
            "introducedDate": "2024-01-15",
            "latestAction": {
                "actionDate": "2024-06-01T10:00:00Z"
            }
        }

        result = provider._normalize_bill(bill_data)

        assert result["introduced_date"] is not None
        assert result["latest_action_date"] is not None


class TestCongressGovProviderRateLimit:
    """Test rate limiting functionality."""

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_get_rate_limit_stats(self, mock_settings):
        """Test getting rate limit statistics."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()
        stats = provider.get_rate_limit_stats()

        assert isinstance(stats, dict)

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_reset_rate_limit_stats(self, mock_settings):
        """Test resetting rate limit statistics."""
        mock_settings_instance = Mock()
        mock_settings_instance.congress_api_key = "test-key"
        mock_settings.return_value = mock_settings_instance

        provider = CongressGovProvider()
        provider.reset_rate_limit_stats()

        # Should not raise exception
        stats = provider.get_rate_limit_stats()
        assert isinstance(stats, dict)


class TestCongressGovProviderIntegration:
    """Integration tests for CongressGovProvider."""

    @patch('fbx_core.providers.congress_gov.Settings')
    def test_full_workflow_dry_run(self, mock_settings, tmp_path):
        """Test full workflow in dry-run mode."""
        mock_settings_instance = Mock()
        mock_settings_instance.dry_run = True
        mock_settings_instance.congress_api_key = None
        mock_settings.return_value = mock_settings_instance

        # Create fixture
        fixtures_dir = tmp_path / "fixtures"
        fixtures_dir.mkdir()
        fixture_file = fixtures_dir / "congress_gov_became_law_sample.json"

        fixture_data = {
            "results": [
                {
                    "congress": 118,
                    "billType": "hr",
                    "billNumber": 1234,
                    "title": "Test Bill",
                    "summary": "Test summary",
                    "laws": [{"number": "118-1"}],
                }
            ]
        }
        fixture_file.write_text(json.dumps(fixture_data))

        provider = CongressGovProvider(fixtures_dir=str(fixtures_dir))
        bills = list(provider.fetch_bills_updated_since(None))

        assert len(bills) == 1
        bill = bills[0]
        assert isinstance(bill, BillRecord)
        assert bill["congress"] == 118
        assert bill["bill_type"] == "hr"
        assert bill["number"] == 1234

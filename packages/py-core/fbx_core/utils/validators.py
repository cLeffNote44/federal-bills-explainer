"""
Input validation utilities for API endpoints.

Provides decorators and functions for validating and sanitizing user input.
"""

import re
from typing import Optional
from fastapi import HTTPException


class ValidationError(HTTPException):
    """Custom validation error."""
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks.

    Args:
        value: Input string
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValidationError: If input is invalid
    """
    if not value:
        return value

    # Check length
    if len(value) > max_length:
        raise ValidationError(f"Input too long. Maximum {max_length} characters allowed.")

    # Remove control characters
    value = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)

    # Trim whitespace
    value = value.strip()

    return value


def validate_congress_number(congress: int) -> int:
    """
    Validate US Congress number.

    Args:
        congress: Congress number to validate

    Returns:
        Validated congress number

    Raises:
        ValidationError: If congress number is invalid
    """
    if congress < 1 or congress > 200:
        raise ValidationError(
            f"Invalid congress number: {congress}. Must be between 1 and 200."
        )
    return congress


def validate_bill_type(bill_type: str) -> str:
    """
    Validate bill type.

    Args:
        bill_type: Bill type to validate (hr, s, hjres, sjres, hconres, sconres, hres, sres)

    Returns:
        Validated bill type in lowercase

    Raises:
        ValidationError: If bill type is invalid
    """
    valid_types = ["hr", "s", "hjres", "sjres", "hconres", "sconres", "hres", "sres"]
    bill_type_lower = bill_type.lower()

    if bill_type_lower not in valid_types:
        raise ValidationError(
            f"Invalid bill type: {bill_type}. Must be one of {valid_types}."
        )

    return bill_type_lower


def validate_bill_number(number: int) -> int:
    """
    Validate bill number.

    Args:
        number: Bill number to validate

    Returns:
        Validated bill number

    Raises:
        ValidationError: If bill number is invalid
    """
    if number < 1 or number > 99999:
        raise ValidationError(
            f"Invalid bill number: {number}. Must be between 1 and 99999."
        )
    return number


def validate_status(status: str) -> str:
    """
    Validate bill status.

    Args:
        status: Bill status to validate

    Returns:
        Validated status

    Raises:
        ValidationError: If status is invalid
    """
    valid_statuses = [
        "introduced",
        "passed",
        "enacted",
        "became-law",
        "vetoed",
        "failed",
        "active",
    ]

    status_lower = status.lower()
    if status_lower not in valid_statuses:
        raise ValidationError(
            f"Invalid status: {status}. Must be one of {valid_statuses}."
        )

    return status_lower


def validate_sort_field(field: str) -> str:
    """
    Validate sort field name.

    Args:
        field: Field name to validate

    Returns:
        Validated field name

    Raises:
        ValidationError: If field name is invalid
    """
    valid_fields = ["date", "congress", "number", "status", "title"]

    if field not in valid_fields:
        raise ValidationError(
            f"Invalid sort field: {field}. Must be one of {valid_fields}."
        )

    return field


def validate_sort_order(order: str) -> str:
    """
    Validate sort order.

    Args:
        order: Sort order to validate (asc or desc)

    Returns:
        Validated sort order

    Raises:
        ValidationError: If sort order is invalid
    """
    order_lower = order.lower()

    if order_lower not in ["asc", "desc"]:
        raise ValidationError(
            f"Invalid sort order: {order}. Must be 'asc' or 'desc'."
        )

    return order_lower


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        page: Page number (1-indexed)
        page_size: Number of items per page
        max_page_size: Maximum allowed page size

    Returns:
        Tuple of (validated_page, validated_page_size)

    Raises:
        ValidationError: If pagination parameters are invalid
    """
    if page < 1:
        raise ValidationError("Page number must be >= 1")

    if page_size < 1:
        raise ValidationError("Page size must be >= 1")

    if page_size > max_page_size:
        raise ValidationError(
            f"Page size too large. Maximum {max_page_size} items per page."
        )

    return page, page_size


def validate_date_range(date_from: Optional[str], date_to: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """
    Validate date range.

    Args:
        date_from: Start date (ISO format)
        date_to: End date (ISO format)

    Returns:
        Tuple of (validated_date_from, validated_date_to)

    Raises:
        ValidationError: If date range is invalid
    """
    if date_from and date_to and date_from > date_to:
        raise ValidationError("date_from must be before or equal to date_to")

    # Validate ISO date format
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'

    if date_from and not re.match(date_pattern, date_from):
        raise ValidationError(f"Invalid date_from format: {date_from}. Use ISO format (YYYY-MM-DD).")

    if date_to and not re.match(date_pattern, date_to):
        raise ValidationError(f"Invalid date_to format: {date_to}. Use ISO format (YYYY-MM-DD).")

    return date_from, date_to


def sanitize_search_query(query: str, max_length: int = 500) -> str:
    """
    Sanitize search query to prevent SQL injection and XSS.

    Args:
        query: Search query
        max_length: Maximum query length

    Returns:
        Sanitized query

    Raises:
        ValidationError: If query is invalid
    """
    if not query:
        return ""

    # Check length
    if len(query) > max_length:
        raise ValidationError(f"Search query too long. Maximum {max_length} characters.")

    # Remove potentially dangerous characters
    query = sanitize_string(query, max_length)

    # Prevent SQL injection attempts
    dangerous_patterns = [
        r"(?i)(\bUNION\s+SELECT\b)",
        r"(?i)(\bDROP\s+TABLE\b)",
        r"(?i)(\bDELETE\s+FROM\b)",
        r"(?i)(\bINSERT\s+INTO\b)",
        r"(?i)(\bEXEC\b|\bEXECUTE\b)",
        r"--",  # SQL comments
        r";.*--",  # SQL command termination with comment
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, query):
            raise ValidationError(
                "Search query contains potentially dangerous patterns. "
                "Please use only alphanumeric characters and basic punctuation."
            )

    return query


def validate_export_limit(limit: int, max_limit: int = 10000) -> int:
    """
    Validate export limit to prevent server overload.

    Args:
        limit: Requested export limit
        max_limit: Maximum allowed limit

    Returns:
        Validated limit

    Raises:
        ValidationError: If limit is invalid
    """
    if limit < 1:
        raise ValidationError("Export limit must be >= 1")

    if limit > max_limit:
        raise ValidationError(
            f"Export limit too large. Maximum {max_limit} records per export. "
            f"Please use pagination or filters to reduce the dataset."
        )

    return limit

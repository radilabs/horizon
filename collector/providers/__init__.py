"""Shared provider errors and helpers."""

from __future__ import annotations


class ProviderError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def error_payload(provider_id: str, display_name: str, code: str, message: str) -> dict:
    return {
        "provider": provider_id,
        "displayName": display_name,
        "plan": None,
        "remainingPercent": None,
        "resetAt": None,
        "status": code,
        "error": message,
    }

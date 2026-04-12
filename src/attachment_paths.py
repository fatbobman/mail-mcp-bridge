#!/usr/bin/env python3
"""
Helpers for safely mapping message IDs onto attachment directories.
"""

import base64
from pathlib import Path
from typing import Union


def normalize_message_id(message_id: str) -> str:
    """
    Normalize a Message-ID for use as a directory name.

    Message-ID values are untrusted input. We only allow a single path segment
    after stripping optional angle brackets.
    """
    clean_message_id = message_id.strip().strip('<>')

    if not clean_message_id:
        raise ValueError("Message-ID is empty")

    return clean_message_id


def get_message_dir_name(message_id: str) -> str:
    """
    Encode a Message-ID into a single safe directory name.
    """
    clean_message_id = normalize_message_id(message_id)
    encoded = base64.urlsafe_b64encode(clean_message_id.encode("utf-8")).decode("ascii")
    return f"mid_{encoded.rstrip('=')}"


def get_message_dir(base_dir: Union[str, Path], message_id: str) -> Path:
    """
    Resolve the directory for a Message-ID and ensure it stays under base_dir.
    """
    base_path = Path(base_dir).resolve(strict=False)
    message_dir_name = get_message_dir_name(message_id)
    message_dir = (base_path / message_dir_name).resolve(strict=False)

    try:
        message_dir.relative_to(base_path)
    except ValueError as exc:
        raise ValueError("Message-ID resolves outside the attachment directory") from exc

    return message_dir

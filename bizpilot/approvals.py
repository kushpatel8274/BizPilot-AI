"""Approval objects for save and data-change operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


class ApprovalAction(str, Enum):
    SAVE_DRAFT = "save_draft"
    CHANGE_BUSINESS_DATA = "change_business_data"


@dataclass(frozen=True)
class ApprovalRequest:
    action: ApprovalAction
    summary: str
    payload: dict
    request_id: str
    created_at: str


def create_approval(action: ApprovalAction, summary: str, payload: dict) -> ApprovalRequest:
    if not summary.strip():
        raise ValueError("Approval summary is required.")
    if not isinstance(payload, dict) or not payload:
        raise ValueError("Approval payload is required.")
    return ApprovalRequest(
        action=action,
        summary=summary.strip(),
        payload=payload,
        request_id=str(uuid4()),
        created_at=datetime.now(timezone.utc).isoformat(),
    )

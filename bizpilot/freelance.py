"""Freelancer-facing draft generation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .ai import OllamaClient, grounded_prompt


@dataclass(frozen=True)
class FreelanceRequest:
    business_name: str
    client_name: str
    service: str
    amount: str = ""
    due_date: str = ""
    tone: str = "professional"
    notes: str = ""

    def facts(self) -> dict[str, str]:
        return {
            "business_name": self.business_name.strip(),
            "client_name": self.client_name.strip(),
            "service": self.service.strip(),
            "amount": self.amount.strip() or "[missing]",
            "due_date": self.due_date.strip() or "[missing]",
            "tone": self.tone.strip() or "professional",
            "notes": self.notes.strip() or "[missing]",
        }


def validate_request(request: FreelanceRequest, require_amount: bool = False) -> None:
    missing = []
    if not request.business_name.strip():
        missing.append("business name")
    if not request.client_name.strip():
        missing.append("client name")
    if not request.service.strip():
        missing.append("service")
    if require_amount and not request.amount.strip():
        missing.append("amount")
    if missing:
        raise ValueError("Missing required details: " + ", ".join(missing) + ".")


def generate_proposal(client: OllamaClient, request: FreelanceRequest) -> str:
    validate_request(request)
    return client.generate(grounded_prompt("Write a concise freelancer proposal.", request.facts()))


def generate_email(client: OllamaClient, request: FreelanceRequest) -> str:
    validate_request(request)
    return client.generate(grounded_prompt("Write a client email draft.", request.facts()))


def generate_quotation(client: OllamaClient, request: FreelanceRequest) -> str:
    validate_request(request, require_amount=True)
    return client.generate(
        grounded_prompt("Write a quotation with scope and total amount.", request.facts())
    )


def generate_payment_reminder(client: OllamaClient, request: FreelanceRequest) -> str:
    validate_request(request, require_amount=True)
    return client.generate(
        grounded_prompt("Write a polite payment reminder.", request.facts())
    )

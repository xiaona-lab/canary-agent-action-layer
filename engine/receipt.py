"""
Receipt Generator — creates verifiable records of executed agent actions.

Receipts are append-only and record what actually happened.
"""

from datetime import datetime, timezone
from typing import Any
import json

class ReceiptGenerator:
    def __init__(self):
        self.receipt_count = 0

    def generate(self, intent: dict, policy_result: dict, execution_result: dict, attribution: dict) -> dict:
        self.receipt_count += 1
        receipt_id = f"rec_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self.receipt_count}"

        receipt = {
            "receipt_id": receipt_id,
            "intent": {
                "agent_id": intent.get("agent", {}).get("id", ""),
                "agent_name": intent.get("agent", {}).get("name", ""),
                "action": intent.get("action", ""),
                "target": intent.get("target", {}),
                "reasoning": intent.get("context", {}).get("reasoning", ""),
                "formed_at": intent.get("timestamp", "")
            },
            "policy_result": {
                "effect": policy_result.get("effect", "deny"),
                "rule_id": policy_result.get("matched_rule", {}).get("rule_id", ""),
                "principal": policy_result.get("matched_rule", {}).get("principal", ""),
                "human_approved": execution_result.get("human_approved", False),
                "human_approval_at": execution_result.get("human_approval_at", None),
                "evaluated_at": policy_result.get("evaluated_at", "")
            },
            "execution": {
                "status": execution_result.get("status", "pending"),
                "evidence": execution_result.get("evidence", []),
                "errors": execution_result.get("errors", []),
                "executed_at": execution_result.get("executed_at", ""),
                "duration_ms": execution_result.get("duration_ms", None)
            },
            "attribution": {
                "initiated_by": attribution.get("initiated_by", ""),
                "authorized_by": attribution.get("authorized_by", ""),
                "policy_version": attribution.get("policy_version", ""),
                "lab": attribution.get("lab", "Xiaona-Lab")
            },
            "status": self._compute_status(policy_result, execution_result),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        return receipt

    def _compute_status(self, policy_result: dict, execution: dict) -> str:
        effect = policy_result.get("effect", "")
        if effect == "deny":
            return "policy_denied"
        if effect == "require_human" and not execution.get("human_approved"):
            return "human_pending"
        if execution.get("status") == "executed":
            return "executed"
        if execution.get("status") == "failed":
            return "failed"
        if execution.get("errors"):
            return "partial"
        return "pending"

    def to_json(self, receipt: dict) -> str:
        return json.dumps(receipt, indent=2, default=str)

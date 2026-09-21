"""
Agent Action Layer — Canary
Orchestrator: Intent → Policy → Authority → Execute → Receipt

Usage:
    python -m engine.pipeline --intent '{"action":"submit_bounty",...}'
"""

from datetime import datetime, timezone
from typing import Any
import json, uuid, time

from .policy import PolicyEngine
from .receipt import ReceiptGenerator

class ActionPipeline:
    def __init__(self, authority_config: dict):
        self.policy = PolicyEngine(authority_config)
        self.receipts = ReceiptGenerator()
        self.attribution = {
            "lab": authority_config.get("principal", "").split("@")[-1] if "@" in authority_config.get("principal", "") else "Xiaona-Lab"
        }

    def run(self, intent: dict, executor: callable = None, human_approved: bool = False,
            human_approval_at: str = None) -> dict:
        # 1. Ensure intent has an ID
        if "intent_id" not in intent:
            intent["intent_id"] = str(uuid.uuid4())

        # 2. Evaluate policy
        policy_result = self.policy.evaluate(intent)

        # 3. If denied, return receipt immediately
        if policy_result["effect"] == "deny":
            return self.receipts.generate(
                intent, policy_result,
                {"status": "skipped", "evidence": [], "errors": ["Blocked by policy"]},
                self.attribution
            )

        # 4. If human required but not approved, return pending receipt
        if policy_result["effect"] == "require_human" and not human_approved:
            return self.receipts.generate(
                intent, policy_result,
                {"status": "pending", "evidence": [], "errors": [],
                 "human_approved": False},
                self.attribution
            )

        # 5. Execute
        if executor:
            start = time.time()
            try:
                exec_result = executor(intent)
                exec_result["duration_ms"] = int((time.time() - start) * 1000)
                exec_result["human_approved"] = human_approved
                exec_result["human_approval_at"] = human_approval_at
                exec_result["executed_at"] = datetime.now(timezone.utc).isoformat()
            except Exception as e:
                exec_result = {
                    "status": "failed", "evidence": [], "errors": [str(e)],
                    "human_approved": human_approved,
                    "executed_at": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": int((time.time() - start) * 1000)
                }
        else:
            exec_result = {
                "status": "pending", "evidence": [], "errors": [],
                "human_approved": human_approved,
                "executed_at": datetime.now(timezone.utc).isoformat()
            }

        # 6. Generate receipt
        receipt = self.receipts.generate(intent, policy_result, exec_result, self.attribution)
        return receipt

    def to_json(self, receipt: dict) -> str:
        return self.receipts.to_json(receipt)

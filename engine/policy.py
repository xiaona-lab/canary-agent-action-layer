"""
Policy Engine — evaluates agent intents against authority rules.

Authority levels:
  allow          → agent can execute autonomously
  deny           → agent cannot execute; blocked
  require_human  → agent must get human approval before executing
  notify         → agent can execute; principal is notified
"""

from datetime import datetime, timezone
from typing import Any

class PolicyEngine:
    def __init__(self, authority_config: dict):
        self.config = authority_config
        self.rules = authority_config.get("policy_rules", [])
        self.default_effect = authority_config.get("default_effect", "deny")

    def evaluate(self, intent: dict) -> dict:
        action_type = intent.get("action", "other")
        platform = intent.get("target", {}).get("platform", "")
        parameters = intent.get("parameters", {})

        matched_rule = None
        conditions_checked = []

        for rule in self.rules:
            if action_type not in rule.get("action_type", []):
                continue

            conditions = rule.get("conditions", {})
            all_passed = True

            # Check max_value
            max_val = conditions.get("max_value")
            if max_val is not None:
                val = self._extract_value(parameters)
                passed = val is None or val <= max_val
                conditions_checked.append({
                    "condition": f"max_value <= {max_val}",
                    "passed": passed,
                    "detail": f"action value: {val}" if val else "no value"
                })
                if not passed:
                    all_passed = False

            # Check platform restriction
            allowed_platforms = conditions.get("platforms")
            if allowed_platforms:
                passed = platform in allowed_platforms
                conditions_checked.append({
                    "condition": f"platform in {allowed_platforms}",
                    "passed": passed,
                    "detail": f"target platform: {platform}"
                })
                if not passed:
                    all_passed = False

            if all_passed:
                matched_rule = rule
                break

        if matched_rule:
            effect = matched_rule["effect"]
        else:
            effect = self.default_effect

        return {
            "intent_id": intent.get("intent_id", ""),
            "effect": effect,
            "matched_rule": {
                "rule_id": matched_rule["rule_id"] if matched_rule else "default",
                "principal": self.config.get("principal", ""),
                "reason": matched_rule.get("reason", "No matching rule") if matched_rule else "Default rule applied"
            } if matched_rule or effect != "allow" else None,
            "conditions_checked": conditions_checked,
            "human_required_reason": self._human_reason(effect, matched_rule) if effect == "require_human" else None,
            "evaluated_at": datetime.now(timezone.utc).isoformat()
        }

    def _extract_value(self, params: dict) -> float | None:
        """Extract monetary value from action parameters."""
        if "reward" in params:
            r = params["reward"]
            if isinstance(r, (int, float)):
                return float(r)
        if "amount" in params:
            a = params["amount"]
            if isinstance(a, (int, float)):
                return float(a)
        if "value" in params:
            v = params["value"]
            if isinstance(v, (int, float)):
                return float(v)
        return None

    def _human_reason(self, effect: str, rule: dict | None) -> str | None:
        if effect != "require_human" or not rule:
            return None
        cond = rule.get("conditions", {})
        human_for = cond.get("require_human_for", [])
        if human_for:
            return f"Human required for: {', '.join(human_for)}"
        return rule.get("reason", "Principal requires human approval for this action type")

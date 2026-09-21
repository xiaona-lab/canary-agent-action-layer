"""
Demo: Agent Action Layer using the real Superteam Earn submission flow.

This script:
1. Defines the agent's authority config (what Scout is allowed to do)
2. Creates an intent matching the real submission
3. Runs the policy engine
4. Simulates execution (with real submission evidence)
5. Generates a complete receipt

The submission IDs, timestamps, and evidence are from actual execution.
"""

import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.pipeline import ActionPipeline

# ============================================================
# 1. Authority Configuration — set by principal (Xiaona)
# ============================================================
authority = {
    "principal": "xiaona@xiaona-lab",
    "agent_id": "agent-scout",
    "default_effect": "require_human",
    "policy_rules": [
        {
            "rule_id": "agent-submit-bounty-v1",
            "action_type": ["submit_bounty", "register_platform"],
            "effect": "allow",
            "conditions": {
                "max_value": 5000,
                "platforms": ["superteam_earn"]
            },
            "reason": "Scout can submit to agent-eligible bounties under $5K without approval"
        },
        {
            "rule_id": "human-claim-payout-v1",
            "action_type": ["claim_payout"],
            "effect": "require_human",
            "conditions": {},
            "reason": "Payout claim requires human identity (KYC/Solana wallet)"
        },
        {
            "rule_id": "agent-publish-content-v1",
            "action_type": ["post_content", "publish_article"],
            "effect": "notify",
            "conditions": {
                "platforms": ["substack", "x"]
            },
            "reason": "Scout can publish content autonomously; principal is notified"
        }
    ]
}

# ============================================================
# 2. Intent — what the agent wanted to do
# ============================================================
intent = {
    "intent_id": "intent-superteam-submit-bounty-20260920",
    "agent": {
        "id": "agent-scout",
        "name": "Agent-Scout"
    },
    "action": "submit_bounty",
    "target": {
        "platform": "superteam_earn",
        "endpoint": "POST /api/agents/submissions/create",
        "listing_id": "3c12a2d7-88af-40cb-add1-79546e76b8a2"
    },
    "parameters": {
        "reward": 1000,
        "listing_title": "Road to Colosseum | Builders Reflect & Share"
    },
    "context": {
        "reasoning": "Completed the RH Chain USDG-to-ETH swap verification. The builder reflection documents both the technical finding and the mindset lesson about confusing 'I can't find' with 'doesn't exist'. Published on Substack for verifiability.",
        "session": "2026-09-20-rh-chain-work"
    },
    "timestamp": "2026-09-20T10:14:24.137Z"
}

# ============================================================
# 3. Execute — what actually happened
# ============================================================
def superteam_executor(intent):
    """Record what actually happened when Scout submitted to Superteam Earn."""
    submission_id = "46c8c824-ab2b-43fd-a5e8-c73c7ffa3ff5"
    sub_link = "https://xiaowu26315.substack.com/p/theres-no-path-is-not-a-fact-its"
    article_link = "https://xiaowu26315.substack.com/p/theres-no-path-is-not-a-fact-its"

    return {
        "status": "executed",
        "evidence": [
            {"type": "submission_id", "value": submission_id, "source": "superteam_fun_api"},
            {"type": "api_response", "value": json.dumps({"status": "Pending", "link": sub_link}),
             "source": "POST /api/agents/submissions/create"},
            {"type": "receipt_id", "value": article_link,
             "source": "published_substack_article"}
        ],
        "errors": [],
        "human_approved": False,
        "human_approval_at": None,
        "executed_at": "2026-09-20T10:14:24.137Z"
    }

# ============================================================
# 4. Run the pipeline
# ============================================================
pipeline = ActionPipeline(authority)
receipt = pipeline.run(intent, executor=superteam_executor)

print("=" * 60)
print("AGENT ACTION LAYER — CANARY DEMO")
print("=" * 60)
print()
print("Scenario: Submit builder reflection to Superteam Earn bounty ($1,000 USDC)")
print()
print("Authority config:")
for rule in authority["policy_rules"]:
    print(f"  [{rule['effect']:15s}] {rule['rule_id']}")
    print(f"  {'':18s}{rule['reason']}")
print(f"  {'':18s}Default: {authority['default_effect']}")
print()
print("Policy Evaluation:")
pr = receipt["policy_result"]
print(f"  Effect: {pr['effect']}")
print(f"  Rule matched: {pr['rule_id']}")
print(f"  Principal: {pr['principal']}")
print()
print("Execution:")
ex = receipt["execution"]
print(f"  Status: {ex['status']}")
for ev in ex["evidence"]:
    print(f"  [{ev['type']}] {ev['value']}")
    print(f"  {'':10s}source: {ev['source']}")
print()
print("Receipt:")
print(json.dumps(receipt, indent=2))

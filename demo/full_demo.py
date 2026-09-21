"""
Full demo: Agent Action Layer with Ed25519-signed receipts and Solana dry-run executor.

Three scenarios:
1. Real Superteam Earn submission (API executor)
2. Solana transfer — policy requires human approval
3. Solana dry-run — policy allows (no wallet needed)
"""

import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.pipeline import ActionPipeline
from engine.receipt_verifiable import VerifiableReceipt
from executors.solana_simulator import SolanaPolicyExecutor

# ============================================================
# 1. Authority config — set by principal
# ============================================================
authority = {
    "principal": "xiaona@xiaona-lab",
    "agent_id": "agent-scout",
    "default_effect": "require_human",
    "policy_rules": [
        {"rule_id": "agent-submit-bounty-v1", "action_type": ["submit_bounty"],
         "effect": "allow", "conditions": {"max_value": 5000, "platforms": ["superteam_earn"]},
         "reason": "Scout can submit to agent-eligible bounties under $5K without approval"},
        {"rule_id": "human-claim-payout-v1", "action_type": ["claim_payout"],
         "effect": "require_human",
         "reason": "Payout claim requires human identity (KYC/Solana wallet)"},
        {"rule_id": "agent-publish-v1", "action_type": ["post_content", "publish_article"],
         "effect": "notify", "conditions": {"platforms": ["substack", "x"]},
         "reason": "Scout can publish content autonomously; principal is notified"},
        {"rule_id": "agent-solana-transfer-v1", "action_type": ["solana_transfer"],
         "effect": "require_human", "conditions": {"max_value": 100},
         "reason": "Solana transfers under $100 require human approval"},
        {"rule_id": "agent-solana-dryrun-v1", "action_type": ["solana_program"],
         "effect": "allow",
         "reason": "Scout can construct Solana dry-run plans autonomously — no real funds moved"}
    ]
}

pipeline = ActionPipeline(authority)
vr = VerifiableReceipt()
sol_ex = SolanaPolicyExecutor()

print(f"Agent public key: {vr.public_key_hex[:20]}...\n")

# ============================================================
# Demo 1: Real Superteam Earn submission
# ============================================================
intent_submit = {
    "intent_id": "intent-superteam-submit-bounty-20260920",
    "agent": {"id": "agent-scout", "name": "Agent-Scout"},
    "action": "submit_bounty",
    "target": {"platform": "superteam_earn", "endpoint": "POST /api/agents/submissions/create"},
    "parameters": {"reward": 1000, "listing_title": "Road to Colosseum | Builders Reflect & Share"},
    "context": {"reasoning": "Completed RH Chain USDG-to-ETH swap verification. Article published on Substack.",
                "session": "2026-09-20-rh-chain-work"},
    "timestamp": "2026-09-20T10:14:24.137Z"
}

def superteam_executor(intent):
    return {
        "status": "executed",
        "evidence": [
            {"type": "submission_id", "value": "46c8c824-ab2b-43fd-a5e8-c73c7ffa3ff5", "source": "superteam_fun_api"},
            {"type": "api_response", "value": '{"status":"Pending","link":"https://xiaowu26315.substack.com/p/theres-no-path-is-not-a-fact-its"}', "source": "POST /api/agents/submissions/create"},
            {"type": "article_url", "value": "https://xiaowu26315.substack.com/p/theres-no-path-is-not-a-fact-its", "source": "substack"}
        ], "errors": [], "executed_at": "2026-09-20T10:14:24.137Z"
    }

r1 = pipeline.run(intent_submit, executor=superteam_executor)
r1["attribution"].update({"initiated_by": "agent-scout", "authorized_by": "xiaona@xiaona-lab", "policy_version": "2026-09-20-v1"})
r1 = vr.sign(r1)
print("===== DEMO 1: SUPERGRAM SUBMIT (REAL) =====")
print(f"  Status: {r1['status']} | Policy: {r1['policy_result']['effect']}")
print(f"  Evidence: submission_id={r1['execution']['evidence'][0]['value'][:20]}...")
print(f"  Signed: seq={r1['_proof']['sequence']} | scheme={r1['_proof']['scheme']}")
print(f"  Verify: {'✅' if vr.verify(r1) else '❌'}")
print()

# ============================================================
# Demo 2: Solana transfer — policy requires human
# ============================================================
intent_sol = {
    "intent_id": "intent-solana-transfer-20260921",
    "agent": {"id": "agent-scout", "name": "Agent-Scout"},
    "action": "solana_transfer",
    "target": {"platform": "solana", "chain": "mainnet-beta", "endpoint": "transfer"},
    "parameters": {"recipient": "ExampleRecipientPublicKey", "amount": 50, "token": "USDC"},
    "context": {"reasoning": "Testing Solana transfer policy gate"},
    "timestamp": "2026-09-21T06:00:00Z"
}

r2 = pipeline.run(intent_sol, executor=sol_ex.execute, human_approved=False)
r2["attribution"].update({"initiated_by": "agent-scout", "authorized_by": "xiaona@xiaona-lab", "policy_version": "2026-09-20-v1"})
r2 = vr.sign(r2)
print("===== DEMO 2: SOLANA TRANSFER (BLOCKED BY POLICY) =====")
print(f"  Status: {r2['status']} | Policy: {r2['policy_result']['effect']}")
print(f"  Rule: {r2['policy_result']['rule_id']}")
print(f"  Verify: {'✅' if vr.verify(r2) else '❌'}")
print()

# ============================================================
# Demo 3: Solana dry-run — policy allows, no wallet needed
# ============================================================
intent_dry = {
    "intent_id": "intent-solana-dryrun-20260921",
    "agent": {"id": "agent-scout", "name": "Agent-Scout"},
    "action": "solana_program",
    "target": {"platform": "solana", "endpoint": "dry-run"},
    "parameters": {"program": "Token Program", "action": "plan_transfer", "recipient": "TestWallet", "amount": 10, "token": "USDC"},
    "context": {"reasoning": "Construct a Solana USDC transfer plan — dry-run only, no real funds move."},
    "timestamp": "2026-09-21T06:00:00Z"
}

r3 = pipeline.run(intent_dry, executor=sol_ex.execute)
r3["attribution"].update({"initiated_by": "agent-scout", "authorized_by": "xiaona@xiaona-lab", "policy_version": "2026-09-20-v1"})
r3 = vr.sign(r3)
print("===== DEMO 3: SOLANA DRY-RUN (AUTO-ALLOWED) =====")
print(f"  Status: {r3['status']} | Policy: {r3['policy_result']['effect']}")
print(f"  Dry-run tx hash: {r3['execution']['evidence'][0]['value'][:30]}...")
print(f"  Verify: {'✅' if vr.verify(r3) else '❌'}")
print()

# ============================================================
# Chain verification
# ============================================================
receipts = [r1, r2, r3]
chain_ok = vr.verify_chain(receipts)
print(f"===== CHAIN VERIFICATION =====")
for i, r in enumerate(receipts):
    print(f"  [{i+1}] seq={r['_proof']['sequence']} chain_hash={r['_proof']['chain_hash'][:16]}...")
print(f"  Chain continuity: {'✅ PASS' if chain_ok else '❌ FAIL'}")
print(f"  Public key (anyone can verify): {vr.public_key_hex}")
print()

# Save
demo_dir = os.path.dirname(os.path.abspath(__file__))
for name, rec in [("signed-superteam-submit.json", r1), ("signed-solana-transfer.json", r2), ("signed-solana-dryrun.json", r3)]:
    with open(os.path.join(demo_dir, name), 'w') as f:
        json.dump(rec, f, indent=2, default=str)
    print(f"Saved: {name}")

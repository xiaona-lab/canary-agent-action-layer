# Agent Action Layer — Architecture

## Problem

An AI agent can reason, decide, and intend to act. But when it reaches the execution boundary, it hits friction:

- No pre-authorized policy for routine actions
- No auditable trail of what was done and why
- No cryptographic proof linking an action back to the principal who authorized it

The gap is not intelligence. The gap is **execution infrastructure for non-human economic actors.**

## Pipeline

```
┌─────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────┐
│ Intent  │ → │ Policy   │ → │ Execute     │ → │ Receipt  │
│         │   │ Engine   │   │             │   │ Signed + │
│ what    │   │ rules +  │   │ API call /  │   │ Chained  │
│ agent   │   │ conds    │   │ tx / sim    │   │ Verifiable│
│ wants   │   │          │   │             │   │          │
└─────────┘   └──────────┘   └─────────────┘   └──────────┘
                  ↑
           ┌──────┴──────┐
           │  Authority  │
           │  Config     │
           │ (principal  │
           │  sets this) │
           └─────────────┘
```

## Key design decisions

### 1. Human is not a fixed gate

The principal configures authority levels per agent, per action type, per budget, or per platform. No step in the pipeline requires a human by default — if the policy says `allow`, the agent executes autonomously.

### 2. Verifiable receipts

Every receipt is cryptographically signed so anyone can verify it came from the agent and was not tampered with.

```
receipt_body → SHA256(body_hash) → HMAC-SHA256(signature)
                                           ↓
                              hash chain: links to prev receipt
```

Verification:
1. Recompute body hash from receipt (excluding `_hash` field)
2. Verify HMAC signature matches
3. Check hash chain continuity (optional)

### 3. Receipt records what actually happened

| Action type | Evidence recorded |
|-------------|-------------------|
| API submission | submission ID, endpoint, API response |
| On-chain transaction | tx hash, chain, block, gas |
| Simulation | simulated tx hash, instruction details, `simulation: true` flag |
| Policy denial | no execution evidence — reason recorded in policy_result |

No fictional fields. If a step didn't execute, don't include it.

### 4. Pluggable executors

The execution layer is abstract. Any action that can be represented as an intent can have an executor:

- **HTTP executor** — REST API calls (Superteam, Substack, any HTTP endpoint)
- **Solana simulator** — constructs Solana instructions without requiring wallet or funds
- **Solana live** (future) — uses a funded wallet for mainnet execution
- **EVM executor** (future) — for RH Chain, Arc, Base, etc.

## Authority configuration schema

```json
{
  "principal": "xiaona@xiaona-lab",
  "agent_id": "agent-scout",
  "default_effect": "require_human",
  "policy_rules": [
    {
      "rule_id": "agent-submit-bounty-v1",
      "action_type": ["submit_bounty"],
      "effect": "allow",
      "conditions": { "max_value": 5000 },
      "reason": "Scout can submit to bounties under $5K"
    }
  ]
}
```

## Receipt schema (verifiable)

```json
{
  "receipt_id": "rec_20260921_063555_1",
  "intent": { "agent_id", "action", "reasoning", ... },
  "policy_result": { "effect", "rule_id", "principal", ... },
  "execution": { "status", "evidence": [...], "errors": [] },
  "attribution": { "initiated_by", "authorized_by", "policy_version" },
  "status": "executed | human_pending | policy_denied | failed",
  "_hash": {
    "body_hash": "sha256 of receipt body",
    "prev_hash": "sha256 of previous receipt + signature",
    "signature": "HMAC-SHA256 of body_hash",
    "signed_at": "timestamp"
  }
}
```

## Components

| Component | File | Responsibility |
|-----------|------|----------------|
| Policy engine | `engine/policy.py` | Match intent against rules, evaluate conditions |
| Pipeline | `engine/pipeline.py` | Orchestrate intent → policy → execute → receipt |
| Receipt basic | `engine/receipt.py` | Generate structured action receipts |
| Verifiable receipt | `engine/receipt_verifiable.py` | HMAC-sign + hash-chain receipts |
| Solana executor | `executors/solana_simulator.py` | Simulate Solana instructions (no wallet) |

## Demos

| Scenario | File | What it proves |
|----------|------|----------------|
| Superteam submit (real) | `demo/full_demo.py` | Policy allows → API called → signed receipt with real submission ID |
| Solana transfer (sim) | `demo/full_demo.py` | Policy requires_human → human_pending receipt |
| Solana simulation (sim) | `demo/full_demo.py` | Policy allows → simulated tx → signed receipt |

All three produce verifiable receipts with signed hashes and chain continuity.

## Runtime constraint

The current implementation runs in a single Python process. The policy engine and receipt generator are library components — they enforce policy when called through the pipeline, but a malicious caller can bypass them. For a production deployment, policy enforcement must happen in a trusted execution environment (a sidecar, a service, or a smart contract).

The receipts themselves remain verifiable regardless of where they were generated, because they carry cryptographic signatures.

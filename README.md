# Agent Action Layer — Canary

Policy + evidence rail for agent actions.

An AI agent can reason, decide, and intend to act. But when it reaches the execution boundary, it hits friction:

- No pre-authorized policy for routine actions
- No auditable trail of what was done and why
- No cryptographic proof linking an action back to the principal who authorized it

The gap is not intelligence. The gap is **execution infrastructure for non-human economic actors.**

## What this is

A configurable pipeline: **Intent → Policy → Authority → Execute → Receipt**

Each step is optional. The principal controls how much authority the agent has. The system enforces that boundary and produces a tamper-evident, Ed25519-signed receipt for every action.

## Authority levels (configurable per rule)

| Effect | Meaning |
|--------|---------|
| `allow` | Agent executes autonomously |
| `deny` | Action blocked; receipt records the denial |
| `require_human` | Agent pauses; principal must approve |
| `notify` | Agent executes; principal is notified |

The principal sets the policy, not the agent. Default: configurable (safe default: `deny` or `require_human`).

## Verifiable receipts

Every receipt is:
1. **Hashed** — body integrity is provable via SHA256
2. **Signed** — Ed25519 signature; anyone with the agent's public key can verify
3. **Chained** — each receipt links to the previous via hash chain (SHA256 of body_hash + prev_chain_hash)

Anyone with the agent's public key can verify a receipt independently. Hash chain proves receipt ordering and prevents insertion or deletion.

## Executor support

| Executor | Status | Description |
|----------|--------|-------------|
| API (HTTP) | ✅ Live | Any REST API call (used for Superteam Earn submission) |
| Solana (dry-run) | ✅ Policy-gated | Constructs Solana instruction plans; dry-run only, no wallet or runtime execution |
| Solana (live) | ⏳ Future | Requires funded Solana wallet and `simulateTransaction` RPC |
| EVM | ⏳ Future | RH Chain, Arc, Base — existing infrastructure available |

## Demo: three scenarios

Run `python demo/full_demo.py`:

1. **Real Superteam Earn submission** — policy allows, API called, signed receipt generated with real submission ID `46c8c824...ff5` and article URL
2. **Solana transfer ($50 USDC)** — policy requires human approval, receipt status = `human_pending`
3. **Solana program simulation** — policy allows, simulator generates simulated tx hash, receipt signed

All three receipts are saved to `demo/signed-*.json` with HMAC signatures and hash chain links.

## Project structure

```
├── README.md
├── schema/
│   ├── intent.json          # Agent intention structure
│   ├── authority.json       # Authority/policy configuration schema
│   ├── policy.json          # Policy evaluation result schema
│   └── receipt.json         # Action receipt schema
├── engine/
│   ├── policy.py            # Rule matching and condition checking
│   ├── pipeline.py          # Intent → Policy → Execute → Receipt orchestrator
│   ├── receipt.py           # Basic receipt generator
│   └── receipt_verifiable.py # HMAC-signed, hash-chained receipts
├── executors/
│   └── solana_simulator.py  # Solana simulation executor (no wallet needed)
├── demo/
│   ├── full_demo.py         # Three-scenario demo runner
│   ├── signed-superteam-submit.json
│   ├── signed-solana-transfer.json
│   └── signed-solana-simulate.json
└── docs/
    └── architecture.md
```

## Principles

1. **Human is not a fixed gate** — authority is configurable. The same system allows full autonomy, per-action approval, or anything between.
2. **Receipt records what actually happened** — API submission records submission ID; on-chain transaction records tx hash; simulation records simulated hash with `simulation: true` flag. No fictional fields.
3. **Attribution chain** — every receipt links back to the agent, the principal, the specific policy rule, and the lab affiliation.

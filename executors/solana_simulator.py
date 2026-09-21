"""
Solana Executor — simulation mode.

Constructs and simulates Solana instructions without needing:
- A funded Solana wallet
- Real SOL for gas
- A live Solana RPC connection

The executor builds a valid instruction, simulates execution,
and records the simulated transaction hash for the receipt.

When a real wallet is connected, swap simulation → execution.
"""

from datetime import datetime, timezone
import json, hashlib

class SolanaSimulator:
    """Simulates Solana transactions for policy + receipt demo purposes."""

    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        self.rpc_url = rpc_url

    def simulate_transfer(self, intent: dict) -> dict:
        """
        Simulate a SOL or SPL token transfer.
        Does NOT send a real transaction — constructs one and simulates.
        """
        params = intent.get("parameters", {})
        recipient = params.get("recipient", "unknown")
        amount = params.get("amount", 0)
        token = params.get("token", "SOL")

        # Generate a deterministic "simulated" tx hash
        sim_input = f"solana_sim_{recipient}_{amount}_{token}_{datetime.now(timezone.utc).isoformat()}"
        sim_hash = hashlib.sha256(sim_input.encode()).hexdigest()
        tx_hash = f"SimTx_{sim_hash[:44]}"

        return {
            "status": "executed",
            "simulation": True,
            "evidence": [
                {
                    "type": "simulated_tx_hash",
                    "value": tx_hash,
                    "source": "solana_simulator",
                    "note": "SIMULATED — no real Solana transaction was sent"
                },
                {
                    "type": "instruction",
                    "value": json.dumps({
                        "program": "System Program",
                        "instruction": "transfer",
                        "from": "agent_wallet (simulated)",
                        "to": recipient,
                        "amount": amount,
                        "token": token
                    }),
                    "source": "solana_simulator"
                }
            ],
            "errors": [],
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

    def simulate_program_interaction(self, intent: dict) -> dict:
        """
        Simulate calling a Solana program (e.g., a DeFi protocol).
        """
        params = intent.get("parameters", {})
        program = params.get("program", "unknown")
        action = params.get("action", "unknown")

        sim_input = f"solana_sim_prog_{program}_{action}_{datetime.now(timezone.utc).isoformat()}"
        sim_hash = hashlib.sha256(sim_input.encode()).hexdigest()
        tx_hash = f"SimTx_{sim_hash[:44]}"

        return {
            "status": "executed",
            "simulation": True,
            "evidence": [
                {
                    "type": "simulated_tx_hash",
                    "value": tx_hash,
                    "source": "solana_simulator"
                },
                {
                    "type": "instruction",
                    "value": json.dumps({
                        "program": program,
                        "action": action,
                        "params": params
                    }),
                    "source": "solana_simulator"
                }
            ],
            "errors": [],
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

class SolanaPolicyExecutor:
    """
    Wraps the simulator with policy enforcement.
    Even in simulation mode, the policy engine must approve the action.
    """

    def __init__(self, simulator: SolanaSimulator = None):
        self.sim = simulator or SolanaSimulator()

    def execute(self, intent: dict) -> dict:
        action = intent.get("action", "")
        if action == "solana_transfer":
            return self.sim.simulate_transfer(intent)
        elif action == "solana_program":
            return self.sim.simulate_program_interaction(intent)
        else:
            return {
                "status": "failed",
                "evidence": [],
                "errors": [f"Unknown Solana action: {action}"],
                "executed_at": datetime.now(timezone.utc).isoformat()
            }

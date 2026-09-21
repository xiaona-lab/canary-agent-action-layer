"""
Verifiable Receipt v2 — Ed25519-signed, hash-chained receipts.

Changes from v1 (HMAC):
- Ed25519 key pair: anyone with the public key can verify
- Hash chain: verify() checks continuity across a receipt sequence
- Sequence numbers for ordered verification
"""

from datetime import datetime, timezone
import json, hashlib
from nacl.signing import SigningKey, VerifyKey
from nacl.encoding import HexEncoder

class VerifiableReceipt:
    """Ed25519-signed receipts with hash chain verification."""

    def __init__(self, signing_key: SigningKey = None):
        self.signing_key = signing_key or SigningKey.generate()
        self.verify_key = self.signing_key.verify_key
        self.chain_tip = None  # hash of (prev_body_hash + prev_signature)
        self._sequence = 0

    @property
    def public_key_hex(self) -> str:
        return self.verify_key.encode(encoder=HexEncoder).decode()

    def sign(self, receipt_body: dict) -> dict:
        self._sequence += 1
        body_str = json.dumps(receipt_body, sort_keys=True, default=str)
        body_hash = hashlib.sha256(body_str.encode()).hexdigest()

        # Chain link: SHA256(body_hash + prev_chain_tip)
        chain_input = body_hash + (self.chain_tip or "")
        chain_hash = hashlib.sha256(chain_input.encode()).hexdigest()

        # Sign the chain hash (not just body hash — chain proves ordering)
        signature_bytes = self.signing_key.sign(
            chain_hash.encode(), encoder=HexEncoder
        )
        signature = signature_bytes.signature.decode() if hasattr(signature_bytes, 'signature') else signature_bytes.hex()

        receipt_body["_proof"] = {
            "body_hash": body_hash,
            "chain_hash": chain_hash,
            "prev_chain_hash": self.chain_tip,
            "sequence": self._sequence,
            "signature": signature,
            "signer": self.public_key_hex,
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "scheme": "ed25519"
        }

        self.chain_tip = chain_hash
        return receipt_body

    def verify(self, receipt: dict, prev_receipt: dict = None) -> bool:
        """Verify a single receipt, optionally checking chain continuity with prev_receipt."""
        try:
            proof = receipt.get("_proof", {})
            body = {k: v for k, v in receipt.items() if k != "_proof"}

            # 1. Verify body integrity
            body_str = json.dumps(body, sort_keys=True, default=str)
            expected_body_hash = hashlib.sha256(body_str.encode()).hexdigest()
            if proof.get("body_hash") != expected_body_hash:
                return False

            # 2. Verify chain hash
            prev_chain = proof.get("prev_chain_hash")
            chain_input = expected_body_hash + (prev_chain or "")
            expected_chain_hash = hashlib.sha256(chain_input.encode()).hexdigest()
            if proof.get("chain_hash") != expected_chain_hash:
                return False

            # 3. Verify Ed25519 signature
            sig_hex = proof.get("signature", "")
            signer_hex = proof.get("signer", "")
            try:
                verify_key = VerifyKey(signer_hex, encoder=HexEncoder)
                verify_key.verify(
                    proof["chain_hash"].encode(),
                    bytes.fromhex(sig_hex)
                )
            except Exception:
                return False

            # 4. Optional: check chain continuity with previous receipt
            if prev_receipt:
                prev_proof = prev_receipt.get("_proof", {})
                prev_chain_hash = prev_proof.get("chain_hash")
                if proof.get("prev_chain_hash") != prev_chain_hash:
                    return False

            return True

        except Exception:
            return False

    def verify_chain(self, receipts: list) -> bool:
        """Verify a sequence of receipts in order."""
        for i, receipt in enumerate(receipts):
            prev = receipts[i - 1] if i > 0 else None
            if not self.verify(receipt, prev_receipt=prev):
                return False
        return True

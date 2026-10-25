import hmac
import hashlib
import json
import base64
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger("finpilot.bank.security")


def _b64url_decode(payload_str: str) -> bytes:
    """Decodes standard base64url strings with missing padding."""
    rem = len(payload_str) % 4
    if rem > 0:
        payload_str += "=" * (4 - rem)
    return base64.urlsafe_b64decode(payload_str.encode("utf-8"))


def verify_rebit_jws_signature(
    jws_header_value: str,
    raw_body: bytes,
    secret: Optional[str] = None,
    public_key_pem: Optional[str] = None
) -> bool:
    """
    Verifies a ReBIT detached JSON Web Signature (x-jws-signature).
    ReBIT detached JWS format: '<b64_protected_header>..<b64_signature>'
    """
    if not jws_header_value or ".." not in jws_header_value:
        return False

    parts = jws_header_value.strip().split(".")
    if len(parts) != 3 or parts[1] != "":
        # Must be detached JWS with empty payload segment between dots
        return False

    b64_header, _, b64_sig = parts

    try:
        header_bytes = _b64url_decode(b64_header)
        header_json = json.loads(header_bytes.decode("utf-8"))
        alg = header_json.get("alg", "HS256")
    except Exception as e:
        logger.warning(f"Malformed JWS protected header: {e}")
        return False

    # Detached payload signing input: <b64_header>.<raw_body_base64url> or <b64_header>.<raw_body>
    # Per RFC 7515 Appendix F, the payload is concatenated in place of the empty segment
    payload_b64url = base64.urlsafe_b64encode(raw_body).decode("ascii").rstrip("=")
    signing_input = f"{b64_header}.{payload_b64url}".encode("ascii")

    try:
        sig_bytes = _b64url_decode(b64_sig)

        # 1. Symmetric HMAC verification (HS256) using BANK_WEBHOOK_SECRET
        if alg == "HS256" and secret:
            expected_hmac = hmac.new(
                secret.encode("utf-8"),
                signing_input,
                hashlib.sha256
            ).digest()
            return hmac.compare_digest(sig_bytes, expected_hmac)

        # 2. Asymmetric RSA verification (RS256/PS256) using Finvu public certificate/key
        if alg in ["RS256", "PS256"] and public_key_pem:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.serialization import load_pem_public_key

            pub_key = load_pem_public_key(public_key_pem.encode("utf-8"))
            pad = (
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH)
                if alg == "PS256"
                else padding.PKCS1v15()
            )
            pub_key.verify(sig_bytes, signing_input, pad, hashes.SHA256())
            return True

    except Exception as e:
        logger.warning(f"JWS signature verification failed: {e}")
        return False

    return False


def verify_bank_webhook(
    headers: Dict[str, str],
    raw_body: bytes
) -> bool:
    """
    Validates incoming webhook authenticity according to Finvu & ReBIT AA specifications.
    
    Supported authentication mechanisms:
    1. ReBIT Detached JWS Header: 'x-jws-signature' (or 'X-JWS-Signature')
    2. Finvu Partner Webhook Secret: 'x-webhook-secret' or 'Authorization: Bearer <secret>'
    3. HMAC-SHA256 Payload Signature: 'x-signature: sha256=<hex_digest>'
    """
    configured_secret = getattr(settings, "BANK_WEBHOOK_SECRET", "").strip()
    public_key_pem = getattr(settings, "BANK_FINVU_PUBLIC_KEY", "").strip()

    # Normalize header keys to lowercase
    lower_headers = {k.lower(): v for k, v in headers.items()}
    jws_sig = lower_headers.get("x-jws-signature")
    webhook_secret = lower_headers.get("x-webhook-secret")
    auth_header = lower_headers.get("authorization", "")
    hex_sig = lower_headers.get("x-signature", "")

    # If in strict production and no verification method configured, deny by default
    if settings.ENVIRONMENT == "production" and not configured_secret and not public_key_pem:
        logger.error("BANK_WEBHOOK_SECRET or BANK_FINVU_PUBLIC_KEY must be configured in production.")
        return False

    # 1. Verify ReBIT x-jws-signature if provided
    if jws_sig:
        if verify_rebit_jws_signature(
            jws_header_value=jws_sig,
            raw_body=raw_body,
            secret=configured_secret or None,
            public_key_pem=public_key_pem or None
        ):
            return True

    # 2. Verify shared webhook secret header if configured
    if configured_secret:
        if webhook_secret and hmac.compare_digest(webhook_secret, configured_secret):
            return True

        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
            if hmac.compare_digest(token, configured_secret):
                return True

        if hex_sig.startswith("sha256="):
            provided_hash = hex_sig[7:].strip()
            computed_hash = hmac.new(
                configured_secret.encode("utf-8"),
                raw_body,
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(provided_hash, computed_hash):
                return True

    # In local testing without configured secret and without signatures, deny
    return False

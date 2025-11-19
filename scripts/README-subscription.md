# Subscription processing helper

This folder contains a small helper script to fetch a subscription URL, detect encoding (gzip/base64), count nodes and optionally write a processed subscription file with markers to enable UDP.

Usage examples:

Fetch and count nodes:

  python3 scripts/process_subscription.py -u "https://.../subscribe?token=TOKEN" --count-only

Fetch, inject udp markers and write output:

  python3 scripts/process_subscription.py -u "https://.../subscribe?token=TOKEN" -o ./proxies/subscription-processed.yaml --inject-udp

Automation tips:
- Run this script as a cron job after Clash updates providers, or as a systemd service that runs on startup.
- The script attempts to decode common encodings but may not perfectly reconstruct complex provider-specific YAML. Validate output before using in production.

Security:
- Do NOT commit subscription tokens to the repository. Use environment variables or local-only files for tokens.

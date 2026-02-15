#!/usr/bin/env python3
"""
consume_product.py - Purchase products from x402 marketplace.

Supports:
- product slug: "pussio"
- studio URL: "https://studio.x402layer.cc/pay/pussio"
- API URL: "https://api.x402layer.cc/p/pussio"
- legacy URL: "https://api.x402layer.cc/storage/product/<id>"

Modes:
- private-key (default): Base + Solana supported
- awal: Base payments via AWAL CLI
"""

import json
import sys
from typing import Tuple

import requests

from awal_bridge import awal_pay_url
from network_selection import pick_payment_option
from solana_signing import create_solana_xpayment_from_accept
from wallet_signing import is_awal_mode, load_wallet_address

API_BASE = "https://api.x402layer.cc"
STUDIO_BASE = "https://studio.x402layer.cc"


def resolve_product_url(product_input: str) -> str:
    if product_input.startswith(f"{API_BASE}/p/"):
        return product_input

    if product_input.startswith(f"{API_BASE}/storage/product/"):
        product_id = product_input.rsplit("/", 1)[-1].strip()
        return f"{API_BASE}/p/{product_id}"

    if product_input.startswith(f"{STUDIO_BASE}/pay/"):
        slug = product_input.replace(f"{STUDIO_BASE}/pay/", "").strip("/")
        return f"{API_BASE}/p/{slug}"

    if not product_input.startswith("http"):
        return f"{API_BASE}/p/{product_input}"

    raise ValueError(f"Unknown product URL format: {product_input}")


def _extract_download_fields(result: dict) -> Tuple[str, str]:
    url = result.get("downloadUrl") or result.get("download_url") or ""
    filename = result.get("fileName") or result.get("file_name") or "downloaded_product"
    return url, filename


def consume_product(product_input: str, download_file: bool = False) -> dict:
    print(f"Resolving product: {product_input}")
    api_url = resolve_product_url(product_input)
    print(f"API URL: {api_url}")

    if is_awal_mode():
        wallet = load_wallet_address(required=False)
        headers = {"Accept": "application/json"}
        if wallet:
            headers["x-wallet-address"] = wallet
        print("Payment mode: AWAL (Base)")
        result = awal_pay_url(api_url, method="GET", headers=headers)
        if download_file and isinstance(result, dict):
            download_url, filename = _extract_download_fields(result)
            if download_url:
                file_response = requests.get(download_url, timeout=60)
                if file_response.status_code == 200:
                    with open(filename, "wb") as handle:
                        handle.write(file_response.content)
                    print(f"Downloaded: {filename} ({len(file_response.content)} bytes)")
        return result

    response = requests.get(api_url, headers={"Accept": "application/json"}, timeout=30)

    if response.status_code == 200:
        print("Product is free or already authorized")
        return response.json()

    if response.status_code != 402:
        raise ValueError(f"Unexpected response: {response.status_code} - {response.text}")

    challenge = response.json()
    selected_network, selected_option, signer = pick_payment_option(challenge, context="product purchase")

    try:
        if selected_network == "base":
            if signer is None:
                raise ValueError("Internal error: missing Base signer")
            x_payment = signer.create_x402_payment_header(
                pay_to=selected_option["payTo"],
                amount=int(selected_option["maxAmountRequired"]),
            )
        else:
            x_payment = create_solana_xpayment_from_accept(selected_option)
    except Exception as exc:
        raise ValueError(f"Failed to build {selected_network} payment: {exc}")

    print(f"Payment network used: {selected_network}")

    response = requests.get(
        api_url,
        headers={
            "X-Payment": x_payment,
            "Accept": "application/json",
        },
        timeout=45,
    )

    if response.status_code != 200:
        raise ValueError(f"Payment failed: {response.status_code} - {response.text}")

    result = response.json()

    print("\nProduct purchased successfully")
    download_url, filename = _extract_download_fields(result)
    if download_url:
        print(f"Download URL: {download_url}")

    if download_file and download_url:
        print(f"Downloading file to: {filename}")
        file_response = requests.get(download_url, timeout=60)
        if file_response.status_code == 200:
            with open(filename, "wb") as handle:
                handle.write(file_response.content)
            print(f"Downloaded: {filename} ({len(file_response.content)} bytes)")
        else:
            print(f"Download failed: {file_response.status_code}")

    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python consume_product.py <product-slug-or-url> [--download]")
        print("\nExamples:")
        print("  python consume_product.py pussio")
        print("  python consume_product.py https://studio.x402layer.cc/pay/pussio")
        print("  python consume_product.py pussio --download")
        sys.exit(1)

    product_input = sys.argv[1]
    download_file = "--download" in sys.argv

    try:
        result = consume_product(product_input, download_file=download_file)
        print("\nResult:")
        print(json.dumps(result, indent=2))
    except Exception as exc:
        print(f"\nError: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()

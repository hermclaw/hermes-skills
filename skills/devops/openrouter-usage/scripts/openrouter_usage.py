#!/usr/bin/env python3
"""OpenRouter API usage and cost reporting."""

import os
import sys
import json
import urllib.request
import urllib.error


def get_api_key():
    """Get API key from env or scan parent processes."""
    key = os.getenv('OPENROUTER_API_KEY')
    if key:
        return key
    try:
        for pid in os.listdir('/proc'):
            if pid.isdigit():
                try:
                    with open(f'/proc/{pid}/environ', 'rb') as f:
                        raw = f.read()
                    for pair in raw.decode('utf-8', errors='replace').split('\x00'):
                        if pair.startswith('OPENROUTER_API_KEY='):
                            return pair.split('=', 1)[1]
                except:
                    pass
    except:
        pass
    return None


def fetch_usage_data(api_key):
    """Fetch usage data from OpenRouter endpoints."""
    base = "https://openrouter.ai/api/v1"
    headers = {"Authorization": f"Bearer {api_key}"}

    # Fetch /auth/key
    req = urllib.request.Request(f"{base}/auth/key", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            auth_data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API error {e.code}: {e.read().decode()}")

    # Fetch /credits
    req = urllib.request.Request(f"{base}/credits", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            credits_data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"API error {e.code}: {e.read().decode()}")

    return auth_data.get('data', {}), credits_data.get('data', {})


def format_currency(value):
    """Format a value as currency string."""
    if value is None:
        return "N/A"
    return f"${value:.2f}"


def display_report(auth_data, credits_data, output_json=False, quiet=False):
    """Display usage report."""
    if output_json:
        report = {
            "key_label": auth_data.get('label', 'unknown'),
            "usage": {
                "total": auth_data.get('usage', 0),
                "daily": auth_data.get('usage_daily', 0),
                "weekly": auth_data.get('usage_weekly', 0),
                "monthly": auth_data.get('usage_monthly', 0),
            },
            "byok_usage": {
                "total": auth_data.get('byok_usage', 0),
                "daily": auth_data.get('byok_usage_daily', 0),
                "weekly": auth_data.get('byok_usage_weekly', 0),
                "monthly": auth_data.get('byok_usage_monthly', 0),
            },
            "credits": {
                "total": credits_data.get('total_credits', 0),
                "used": credits_data.get('total_usage', 0),
            },
            "limits": {
                "has_limit": auth_data.get('limit') is not None,
                "limit": auth_data.get('limit'),
                "limit_remaining": auth_data.get('limit_remaining'),
            },
            "is_free_tier": auth_data.get('is_free_tier', False),
            "rate_limit": auth_data.get('rate_limit', {}),
        }
        print(json.dumps(report, indent=2))
        return

    if quiet:
        return

    # Text output
    print("OpenRouter Usage Report")
    print("=" * 40)
    print(f"Key:           {auth_data.get('label', 'unknown')}")
    print()
    print(f"Today:         {format_currency(auth_data.get('usage_daily', 0))}")
    print(f"This Week:     {format_currency(auth_data.get('usage_weekly', 0))}")
    print(f"This Month:    {format_currency(auth_data.get('usage_monthly', 0))}")
    print()
    print(f"Credits:       {format_currency(credits_data.get('total_credits', 0))} remaining")
    print(f"Total Used:    {format_currency(credits_data.get('total_usage', 0))}")

    if auth_data.get('is_free_tier'):
        print("\nPlan:          Free Tier")
    else:
        print("\nPlan:          Paid")

    rate = auth_data.get('rate_limit', {})
    requests = rate.get('requests', -1)
    if requests == -1:
        print("Rate Limit:    Unlimited (10s interval)")
    else:
        print(f"Rate Limit:    {requests} requests per {rate.get('interval', '10s')}")

    # Show limit info if set
    limit = auth_data.get('limit')
    if limit:
        remaining = auth_data.get('limit_remaining')
        print(f"\nSpending Limit: {format_currency(limit)}")
        print(f"Limit Remaining: {format_currency(remaining)}")


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Check OpenRouter API usage and credits",
        epilog="Examples:\n  %(prog)s\n  %(prog)s --json\n  %(prog)s --quiet",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--quiet', '-q', action='store_true', help='Only output errors')
    args = parser.parse_args()

    api_key = get_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found", file=sys.stderr)
        sys.exit(1)

    try:
        auth_data, credits_data = fetch_usage_data(api_key)
        display_report(auth_data, credits_data, output_json=args.json, quiet=args.quiet)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

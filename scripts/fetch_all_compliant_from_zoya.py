#!/usr/bin/env python3
"""
Fetch all compliant stocks/funds from Zoya API using pagination.

This script uses the ZoyaComplianceGateway's get_all_reports method
to retrieve all halal-compliant securities from the Zoya database.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from stock_friend.gateways.compliance.zoya_gateway import ZoyaComplianceGateway
from stock_friend.infrastructure.rate_limiter import RateLimiter


def save_reports_to_file(
    reports: List[Dict],
    output_path: Path,
    asset_type: str,
) -> None:
    """
    Save compliance reports to JSON file.

    Args:
        reports: List of report dictionaries
        output_path: Path to save JSON file
        asset_type: "stock" or "fund"
    """
    output_data = {
        "asset_type": asset_type,
        "total_count": len(reports),
        "reports": reports,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)


def print_summary(reports: List[Dict], asset_type: str) -> None:
    """Print summary statistics about fetched reports."""
    print(f"\n{'=' * 80}")
    print(f"Summary: Compliant {asset_type.capitalize()}s")
    print(f"{'=' * 80}")
    print(f"Total count: {len(reports)}")

    if not reports:
        print("No compliant securities found.")
        return

    # Group by exchange
    by_exchange = {}
    for report in reports:
        exchange = report.get("exchange", "Unknown")
        by_exchange.setdefault(exchange, []).append(report)

    print(f"\nBy Exchange:")
    for exchange, items in sorted(by_exchange.items()):
        print(f"  {exchange:10s}: {len(items):5d} securities")

    # Show first 10 examples
    print(f"\nFirst 10 examples:")
    for report in reports[:10]:
        symbol = report.get("symbol", "N/A")
        name = report.get("name", "N/A")
        exchange = report.get("exchange", "N/A")
        print(f"  {symbol:8s} ({exchange:4s}): {name}")

    if len(reports) > 10:
        print(f"  ... and {len(reports) - 10} more")


def main() -> None:
    """Main execution function."""
    # Load environment variables
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    load_dotenv(env_path)

    # Get API credentials
    api_key = os.getenv("COMPLIANCE_ZOYA_API_KEY")
    environment = os.getenv("COMPLIANCE_ZOYA_ENVIRONMENT", "sandbox")

    if not api_key:
        print("Error: COMPLIANCE_ZOYA_API_KEY not found in .env file")
        sys.exit(1)

    print(f"Fetching compliant securities from Zoya API ({environment} environment)...")
    print(f"This may take a few minutes due to rate limiting (10 requests/second).\n")

    # Create rate limiter to respect Zoya's limits
    rate_limiter = RateLimiter()

    # Create gateway
    gateway = ZoyaComplianceGateway(
        api_key=api_key,
        environment=environment,
        rate_limiter=rate_limiter,
    )

    # Ensure output directory exists
    output_dir = project_root / "data" / "zoya"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Fetch compliant stocks
        print("Fetching compliant stocks...")
        compliant_stocks = gateway.get_all_reports(
            asset_type="stock",
            status_filter="COMPLIANT",
        )

        stocks_file = output_dir / f"compliant_stocks_{environment}.json"
        save_reports_to_file(compliant_stocks, stocks_file, "stock")
        print(f"✓ Saved {len(compliant_stocks)} compliant stocks to: {stocks_file}")
        print_summary(compliant_stocks, "stock")

        # Fetch compliant funds
        print("\nFetching compliant funds...")
        compliant_funds = gateway.get_all_reports(
            asset_type="fund",
            status_filter="COMPLIANT",
        )

        funds_file = output_dir / f"compliant_funds_{environment}.json"
        save_reports_to_file(compliant_funds, funds_file, "fund")
        print(f"✓ Saved {len(compliant_funds)} compliant funds to: {funds_file}")
        print_summary(compliant_funds, "fund")

        # Combined summary
        print(f"\n{'=' * 80}")
        print("Overall Summary")
        print(f"{'=' * 80}")
        print(f"Total compliant stocks: {len(compliant_stocks)}")
        print(f"Total compliant funds:  {len(compliant_funds)}")
        print(f"Total compliant securities: {len(compliant_stocks) + len(compliant_funds)}")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

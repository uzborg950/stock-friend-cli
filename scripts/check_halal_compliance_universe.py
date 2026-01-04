"""
Screen stock universe for halal-compliant stocks using Zoya API.

This script demonstrates end-to-end compliance checking with symbol normalization:
1. Load stock universe from CSV
2. Check compliance for each stock via Zoya API
3. Apply symbol normalization for European stocks
4. Export compliant stocks to CSV

Usage:
    python scripts/screen_sp500_halal.py <input_csv> [output_csv]

Examples:
    python scripts/screen_sp500_halal.py data/universes/sp500_constituents.csv
    python scripts/screen_sp500_halal.py data/universes/nasdaq100_constituents.csv data/compliance/nasdaq100_halal.csv
"""
import argparse
import csv
import sys
import time
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from stock_friend.gateways.compliance import ZoyaComplianceGateway
from stock_friend.services.compliance_service import ComplianceService
from stock_friend.services.symbol_normalization_service import (
    SymbolNormalizationService,
)

# Default configuration
ZOYA_ENVIRONMENT = "sandbox" #sandbox or live

# Rate limiting (10 req/sec = 0.1s per request, but add buffer)
REQUEST_DELAY = 0.15  # 150ms between requests

def load_universe(csv_path):
    """Load stock universe from CSV."""
    stocks = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("ticker"):  # Skip empty rows
                stocks.append(row)
    return stocks

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Screen stock universe for halal-compliant stocks using Zoya API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/screen_sp500_halal.py data/universes/sp500_constituents.csv
  python scripts/screen_sp500_halal.py data/universes/nasdaq100_constituents.csv data/compliance/nasdaq100_halal.csv
        """
    )
    parser.add_argument(
        "input_csv",
        type=str,
        help="Path to input CSV file containing stocks (must have ticker, company_name, sector, industry columns)"
    )
    parser.add_argument(
        "output_csv",
        type=str,
        nargs="?",
        help="Path to output CSV file for halal-compliant stocks (optional, defaults to data/compliance/<input_name>_halal.csv)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="Zoya API key (defaults to sandbox key)"
    )
    parser.add_argument(
        "--environment",
        type=str,
        choices=["sandbox", "live"],
        default=ZOYA_ENVIRONMENT,
        help="Zoya API environment (default: sandbox)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY,
        help=f"Delay between API requests in seconds (default: {REQUEST_DELAY})"
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Resolve paths
    input_path = Path(args.input_csv)
    if not input_path.is_absolute():
        input_path = project_root / input_path

    if not input_path.exists():
        print(f"✗ Error: Input file not found: {input_path}")
        sys.exit(1)

    # Determine output paths
    if args.output_csv:
        output_path = Path(args.output_csv)
        if not output_path.is_absolute():
            output_path = project_root / output_path
    else:
        # Default: data/compliance/<input_name>_halal.csv
        input_stem = input_path.stem.replace("_constituents", "")
        output_path = project_root / "data" / "compliance" / f"{input_stem}_halal.csv"

    full_results_path = output_path.parent / f"{output_path.stem}_full_results.csv"

    # Print configuration
    print("=" * 80)
    print("HALAL COMPLIANCE SCREENING")
    print("=" * 80)
    print(f"\nInput:        {input_path}")
    print(f"Output:       {output_path}")
    print(f"Full Results: {full_results_path}")
    print(f"\nZoya API:     {args.environment.upper()}")
    print(f"Rate Limit:   {1/args.delay:.1f} requests/second")

    # Load universe
    print(f"\n{'=' * 80}")
    print("STEP 1: Loading Stock Universe")
    print("=" * 80)

    stocks = load_universe(input_path)
    print(f"✓ Loaded {len(stocks)} stocks")

    # Initialize services
    print(f"\n{'=' * 80}")
    print("STEP 2: Initializing Compliance Services")
    print("=" * 80)

    gateway = ZoyaComplianceGateway(
        api_key=args.api_key,
        environment=args.environment,
    )
    normalizer = SymbolNormalizationService()
    compliance_service = ComplianceService(gateway, normalizer)

    print("✓ ZoyaComplianceGateway initialized")
    print("✓ SymbolNormalizationService initialized")
    print("✓ ComplianceService initialized")

    # Check compliance for all stocks
    print(f"\n{'=' * 80}")
    estimated_time = len(stocks) * args.delay
    print(f"STEP 3: Checking Compliance (Estimated: {estimated_time/60:.1f} minutes)")
    print("=" * 80)

    results = []
    compliant_count = 0
    non_compliant_count = 0
    unknown_count = 0

    for i, stock in enumerate(stocks, 1):
        ticker = stock["ticker"]

        # Progress indicator
        if i % 10 == 0:
            print(f"Progress: {i}/{len(stocks)} stocks checked "
                  f"({compliant_count} compliant, {non_compliant_count} non-compliant, {unknown_count} unknown)")

        try:
            # Create simple stock object (ComplianceService expects object with ticker and exchange attributes)
            class StockData:
                def __init__(self, ticker, exchange=None):
                    self.ticker = ticker
                    self.exchange = exchange

            stock_obj = StockData(ticker)
            status = compliance_service.check_stock_compliance(stock_obj)

            # Count results
            if status.is_compliant is True:
                compliant_count += 1
            elif status.is_compliant is False:
                non_compliant_count += 1
            else:
                unknown_count += 1

            # Store result
            results.append({
                "ticker": ticker,
                "company_name": stock["company_name"],
                "sector": stock["sector"],
                "industry": stock["industry"],
                "is_compliant": status.is_compliant,
                "compliance_score": status.compliance_score if status.compliance_score else "",
                "source": status.source,
                "checked_at": status.checked_at.isoformat(),
            })

            # Rate limiting
            time.sleep(args.delay)

        except Exception as e:
            print(f"\n✗ Error checking {ticker}: {e}")
            results.append({
                "ticker": ticker,
                "company_name": stock["company_name"],
                "sector": stock["sector"],
                "industry": stock["industry"],
                "is_compliant": None,
                "compliance_score": "",
                "source": "error",
                "checked_at": "",
            })

    # Summary
    print(f"\n{'=' * 80}")
    print("STEP 4: Results Summary")
    print("=" * 80)
    print(f"\nTotal Stocks Checked: {len(stocks)}")
    print(f"✓ Compliant:          {compliant_count} ({compliant_count/len(stocks)*100:.1f}%)")
    print(f"✗ Non-Compliant:      {non_compliant_count} ({non_compliant_count/len(stocks)*100:.1f}%)")
    print(f"? Unknown:            {unknown_count} ({unknown_count/len(stocks)*100:.1f}%)")

    # Export full results
    print(f"\n{'=' * 80}")
    print("STEP 5: Exporting Results")
    print("=" * 80)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export full results
    with open(full_results_path, "w", newline="") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"✓ Full results exported: {full_results_path}")

    # Export only compliant stocks
    compliant_results = [r for r in results if r["is_compliant"] is True]
    with open(output_path, "w", newline="") as f:
        if compliant_results:
            writer = csv.DictWriter(f, fieldnames=compliant_results[0].keys())
            writer.writeheader()
            writer.writerows(compliant_results)
    print(f"✓ Halal-compliant stocks exported: {output_path}")
    print(f"  ({len(compliant_results)} stocks)")

    # Show sample compliant stocks
    if compliant_results:
        print(f"\n{'=' * 80}")
        print("Sample Halal-Compliant Stocks:")
        print("=" * 80)
        for stock in compliant_results[:10]:
            score = f"({stock['compliance_score']:.1f}%)" if stock['compliance_score'] else ""
            print(f"  {stock['ticker']:6} - {stock['company_name']:40} {score}")
        if len(compliant_results) > 10:
            print(f"  ... and {len(compliant_results) - 10} more")

    print(f"\n{'=' * 80}")
    print("✅ SCREENING COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to:")
    print(f"  - All stocks: {full_results_path}")
    print(f"  - Halal only: {output_path}")

if __name__ == "__main__":
    main()

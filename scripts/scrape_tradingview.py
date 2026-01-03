#!/usr/bin/env python3
"""
TradingView Index/ETF Constituents Scraper

Scrapes constituent data from TradingView index/ETF components pages.

Usage:
    python scripts/scrape_tradingview.py --url "https://www.tradingview.com/symbols/SPX/components/" --output "sp500"
    python scripts/scrape_tradingview.py --url "https://www.tradingview.com/symbols/NDAQ/components/" --output "nasdaq"
"""

import argparse
import csv
import time
from pathlib import Path
from typing import List, Dict, Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def setup_chrome_driver() -> webdriver.Chrome:
    """
    Set up Chrome WebDriver by connecting to existing Chrome session.

    Requires Chrome to be running with remote debugging on port 9222.

    Returns:
        Chrome WebDriver instance

    Raises:
        Exception: If cannot connect to Chrome on port 9222
    """
    chrome_options = Options()

    # Connect to existing Chrome session with remote debugging
    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

    print("Connecting to Chrome on port 9222...")

    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✓ Connected to Chrome successfully")
        return driver
    except Exception as e:
        print(f"✗ Could not connect to Chrome: {e}")
        print()
        print("Make sure Chrome is running with remote debugging:")
        print("  /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
        print("    --remote-debugging-port=9222 \\")
        print("    --user-data-dir=\"$(pwd)/remote-profile\" \\")
        print("    --profile-directory=\"Profile 2\"")
        print()
        print("Verify connection: curl http://127.0.0.1:9222/json")
        raise


def wait_for_table_load(driver: webdriver.Chrome, timeout: int = 20) -> bool:
    """
    Wait for the TradingView table to load.

    Args:
        driver: Chrome WebDriver instance
        timeout: Maximum seconds to wait

    Returns:
        True if table loaded successfully
    """
    try:
        print(f"Waiting for table to load (timeout: {timeout}s)...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'tbody[data-testid="selectable-rows-table-body"]')
            )
        )
        print("✓ Table loaded")
        # Wait a bit more for all rows to populate
        time.sleep(2)
        return True
    except TimeoutException:
        print("✗ Timeout waiting for table to load")
        return False


def click_load_more_buttons(driver: webdriver.Chrome, max_clicks: int = 50) -> int:
    """
    Click "Load More" buttons to load all table rows.

    Args:
        driver: Chrome WebDriver instance
        max_clicks: Maximum number of times to click "Load More"

    Returns:
        Total number of "Load More" clicks performed
    """
    print("Looking for 'Load More' button...")

    clicks_performed = 0

    for i in range(max_clicks):
        try:
            # TradingView's "Load More" button selector (found via inspection)
            # Button has data-overflow-tooltip-text="Load More"
            button = driver.find_element(
                By.CSS_SELECTOR,
                'button[data-overflow-tooltip-text="Load More"]'
            )

            if button and button.is_displayed() and button.is_enabled():
                # Scroll button into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(0.5)

                # Click the button
                button.click()
                clicks_performed += 1
                print(f"  Clicked 'Load More' button (click #{clicks_performed})")

                # Wait for new rows to load
                time.sleep(2)
            else:
                # Button not clickable
                print(f"✓ 'Load More' button no longer clickable after {clicks_performed} clicks")
                break

        except Exception as e:
            # Button not found or not clickable anymore
            if clicks_performed == 0:
                print(f"✓ No 'Load More' button found (page may already show all rows)")
            else:
                print(f"✓ Finished clicking 'Load More' ({clicks_performed} clicks total)")
            break

    return clicks_performed


def scroll_to_load_all_rows(driver: webdriver.Chrome, target_rows: int = 503, max_scrolls: int = 50) -> None:
    """
    Scroll down the page to trigger lazy loading of all table rows.

    TradingView uses virtual scrolling - only ~100 rows are rendered at a time.
    We need to scroll multiple times to ensure all data is captured.

    Args:
        driver: Chrome WebDriver instance
        target_rows: Expected total number of rows (from data-matches attribute)
        max_scrolls: Maximum number of scroll attempts
    """
    print(f"Scrolling to load all rows (target: {target_rows})...")

    # Track unique tickers we've seen
    seen_tickers = set()

    def extract_current_tickers():
        """Extract all tickers currently visible in the table."""
        try:
            tbody = driver.find_element(
                By.CSS_SELECTOR,
                'tbody[data-testid="selectable-rows-table-body"]'
            )
            rows = tbody.find_elements(By.TAG_NAME, "tr")
            tickers = []
            for row in rows:
                try:
                    first_cell = row.find_elements(By.TAG_NAME, "td")[0]
                    cell_text = first_cell.text.strip()
                    lines = [line.strip() for line in cell_text.split('\n') if line.strip()]
                    if lines:
                        ticker = ''.join(c for c in lines[0] if c.isalnum() or c == '.')
                        if ticker and len(ticker) <= 10:
                            tickers.append(ticker)
                except:
                    continue
            return tickers
        except:
            return []

    unchanged_count = 0
    max_unchanged = 5  # Stop after 5 scrolls with no new tickers

    for i in range(max_scrolls):
        # Extract tickers before scroll
        current_tickers = extract_current_tickers()
        new_tickers = [t for t in current_tickers if t not in seen_tickers]

        if new_tickers:
            seen_tickers.update(new_tickers)
            print(f"  Scroll {i+1}: {len(seen_tickers)} unique tickers collected (target: {target_rows})")
            unchanged_count = 0
        else:
            unchanged_count += 1

        # Check if we've collected enough tickers
        if len(seen_tickers) >= target_rows:
            print(f"✓ Collected all {len(seen_tickers)} tickers!")
            break

        if unchanged_count >= max_unchanged:
            print(f"✓ No new tickers after {unchanged_count} scrolls. Collected {len(seen_tickers)} total.")
            break

        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # Wait for lazy loading

        # Also try scrolling the table container if it exists
        try:
            driver.execute_script("""
                const table = document.querySelector('tbody[data-testid="selectable-rows-table-body"]');
                if (table && table.parentElement) {
                    table.parentElement.scrollTop = table.parentElement.scrollHeight;
                }
            """)
            time.sleep(1)
        except:
            pass

    # Final extraction after all scrolling
    final_tickers = extract_current_tickers()
    seen_tickers.update(final_tickers)

    print(f"✓ Total unique tickers collected: {len(seen_tickers)}")

    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)


def extract_table_data(driver: webdriver.Chrome) -> List[Dict[str, str]]:
    """
    Extract constituent data from the TradingView table.

    Args:
        driver: Chrome WebDriver instance

    Returns:
        List of dictionaries with stock data
    """
    constituents = []

    try:
        tbody = driver.find_element(
            By.CSS_SELECTOR,
            'tbody[data-testid="selectable-rows-table-body"]'
        )
        rows = tbody.find_elements(By.TAG_NAME, "tr")

        print(f"Found {len(rows)} rows in table")

        for idx, row in enumerate(rows, 1):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")

                if len(cells) < 2:
                    continue

                # Extract ticker and company name from first column
                # TradingView typically has ticker and company name in nested divs/spans
                first_cell = cells[0]
                cell_text = first_cell.text.strip()
                lines = [line.strip() for line in cell_text.split('\n') if line.strip()]

                ticker = ""
                company_name = ""

                if len(lines) >= 2:
                    # Usually: [ticker, company_name, other_data...]
                    ticker = lines[0]
                    company_name = lines[1]
                elif len(lines) == 1:
                    ticker = lines[0]
                    company_name = ticker

                # Extract sector and analyst rating from last two cells
                # TradingView structure: [...prices/metrics...][Sector][Analyst Rating]
                sector = "Unknown"
                industry = "Unknown"

                # Look for sector in cells - it's typically in a link
                for cell in cells:
                    # Find sector links (format: /sectorandindustry-sector/...)
                    links = cell.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if "sectorandindustry-sector" in href:
                            sector = link.text.strip()
                            break
                    if sector != "Unknown":
                        break

                # Industry can be the same as sector for our purposes (TradingView doesn't always show sub-industry)
                industry = sector

                # Clean up ticker (remove any non-alphanumeric except .)
                ticker = ''.join(c for c in ticker if c.isalnum() or c == '.')

                if ticker and len(ticker) <= 10:  # Valid tickers are usually 1-10 chars
                    constituents.append({
                        "ticker": ticker,
                        "company_name": company_name or ticker,
                        "sector": sector,
                        "industry": industry
                    })

                    if idx % 50 == 0:
                        print(f"  Processed {idx} rows...")

            except Exception as e:
                print(f"  Warning: Error parsing row {idx}: {e}")
                continue

        print(f"✓ Extracted {len(constituents)} constituents")
        return constituents

    except NoSuchElementException:
        print("✗ Could not find table body element")
        return []


def save_to_csv(
    constituents: List[Dict[str, str]],
    output_name: str,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Save constituents to CSV file.

    Args:
        constituents: List of constituent data
        output_name: Name for output file (without extension)
        output_dir: Output directory (defaults to data/universes)

    Returns:
        Path to saved CSV file
    """
    if output_dir is None:
        # Default to data/universes relative to script location
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent / "data" / "universes"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{output_name}_constituents.csv"

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["ticker", "company_name", "sector", "industry"]
        )
        writer.writeheader()
        writer.writerows(constituents)

    print(f"✓ Saved to: {output_file}")
    return output_file


def scrape_tradingview_index(
    url: str,
    output_name: str,
    max_scrolls: int = 50,
    save_html_debug: bool = False
) -> Optional[Path]:
    """
    Main function to scrape TradingView index/ETF constituents.

    Args:
        url: TradingView components page URL
        output_name: Name for output CSV file
        max_scrolls: Maximum scrolls to load all data
        save_html_debug: Save page HTML for debugging

    Returns:
        Path to saved CSV file, or None if failed
    """
    driver = None

    try:
        print(f"\n{'='*60}")
        print(f"TradingView Scraper")
        print(f"{'='*60}")
        print(f"URL: {url}")
        print(f"Output: {output_name}_constituents.csv\n")

        # Setup driver
        driver = setup_chrome_driver()

        # Navigate to URL
        print(f"Navigating to: {url}")
        driver.get(url)

        # Wait for table to load
        if not wait_for_table_load(driver):
            print("✗ Failed to load table")
            return None

        # Get target row count from data-matches attribute
        target_rows = 500  # Default
        try:
            tbody = driver.find_element(
                By.CSS_SELECTOR,
                'tbody[data-testid="selectable-rows-table-body"]'
            )
            data_matches = tbody.get_attribute("data-matches")
            if data_matches:
                target_rows = int(data_matches)
                print(f"Target rows to scrape: {target_rows}")
        except:
            print("Could not determine target row count, using default: 500")

        # Click "Load More" buttons to load rows in batches
        clicks = click_load_more_buttons(driver, max_clicks=max_scrolls)

        # Then scroll to load any remaining rows (TradingView also uses virtual scrolling)
        # Use fewer scrolls if button was clicked, more if no button found
        scroll_attempts = 10 if clicks > 0 else max_scrolls
        scroll_to_load_all_rows(driver, target_rows=target_rows, max_scrolls=scroll_attempts)

        # Save HTML for debugging if requested
        if save_html_debug:
            script_dir = Path(__file__).parent
            debug_dir = script_dir.parent / "data" / "debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_file = debug_dir / f"{output_name}_page.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print(f"✓ Saved page HTML to: {debug_file}")

        # Extract data
        constituents = extract_table_data(driver)

        if not constituents:
            print("✗ No constituents extracted")
            return None

        # Save to CSV
        output_file = save_to_csv(constituents, output_name)

        print(f"\n{'='*60}")
        print(f"✓ Successfully scraped {len(constituents)} constituents")
        print(f"{'='*60}\n")

        return output_file

    except Exception as e:
        print(f"\n✗ Error during scraping: {e}")
        return None

    finally:
        # Don't close the browser - we're connected to user's existing session
        pass


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scrape TradingView index/ETF constituents"
    )
    parser.add_argument(
        "--url",
        required=True,
        help="TradingView components page URL"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output file name (without extension)"
    )
    parser.add_argument(
        "--max-scrolls",
        type=int,
        default=50,
        help="Maximum 'Load More' button clicks and scroll attempts (default: 50)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save HTML page source for debugging"
    )

    args = parser.parse_args()

    scrape_tradingview_index(
        url=args.url,
        output_name=args.output,
        max_scrolls=args.max_scrolls,
        save_html_debug=args.debug
    )


if __name__ == "__main__":
    main()

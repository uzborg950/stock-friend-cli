# Scripts Directory

Utility scripts for data collection and maintenance.

## TradingView Scraper

Scrapes up-to-date constituent data from TradingView index/ETF component pages.

### Prerequisites

1. **Chrome with Remote Debugging**

   The project includes a `remote-profile/` directory for a dedicated Chrome profile with remote debugging enabled.

   **Setup (First Time):**

   ```bash
   # Start Chrome with the dedicated remote profile
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir="$(pwd)/remote-profile" \
     --profile-directory="Profile 2"
   ```

   **Important:** Log in to your desired chrome profile AND TradingView on this Chrome instance. The login will be persisted in `remote-profile/Profile 2/`.

   **Subsequent Usage:**

   Just run the same command again - your TradingView login will be remembered:

   ```bash
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
     --remote-debugging-port=9222 \
     --user-data-dir="$(pwd)/remote-profile" \
     --profile-directory="Profile 2"
   ```

   **Verify it's working:**
   ```bash
   curl http://127.0.0.1:9222/json
   # Should return JSON with Chrome DevTools debugging info
   ```

2. **Dependencies Installed**
   ```bash
   poetry install
   ```

### Usage

Make sure Chrome is running with remote debugging (see Prerequisites above), then:

#### Scrape S&P 500 Constituents

```bash
python scripts/scrape_tradingview.py \
  --url "https://www.tradingview.com/symbols/SPX/components/?exchange=CBOE" \
  --output "sp500"
```

#### Scrape NASDAQ-100 Constituents

```bash
python scripts/scrape_tradingview.py \
  --url "https://www.tradingview.com/symbols/NDX/components/" \
  --output "nasdaq100"
```

#### Scrape Russell 2000 Constituents

```bash
python scripts/scrape_tradingview.py \
  --url "https://www.tradingview.com/symbols/RUT/components/" \
  --output "russell2000"
```

#### Scrape Any ETF (e.g., QQQ)

```bash
python scripts/scrape_tradingview.py \
  --url "https://www.tradingview.com/symbols/NASDAQ-QQQ/components/" \
  --output "qqq"
```

### Options

- `--url`: TradingView components page URL (required)
- `--output`: Output file name without extension (required)
- `--max-scrolls`: Maximum "Load More" button clicks and scroll attempts (default: 50)
- `--debug`: Save HTML page source for debugging

### Output

CSV files are saved to `data/universes/` with columns:
- `ticker`: Stock ticker symbol
- `company_name`: Company name
- `sector`: GICS sector
- `industry`: GICS industry

### Examples

```bash
# Basic scraping
python scripts/scrape_tradingview.py \
  --url "https://www.tradingview.com/symbols/SPX/components/" \
  --output "sp500"

# Scrape large index with more scrolls (if needed)
python scripts/scrape_tradingview.py \
  --url "https://www.tradingview.com/symbols/RUT/components/" \
  --output "russell2000" \
  --max-scrolls 100

# Enable debug mode to save HTML for troubleshooting
python scripts/scrape_tradingview.py \
  --url "https://www.tradingview.com/symbols/SPX/components/" \
  --output "sp500" \
  --debug
```

### Troubleshooting

**"Could not connect to Chrome"**
- Make sure Chrome is running with `--remote-debugging-port=9222`
- Verify: `curl http://127.0.0.1:9222/json` should return JSON data
- Check you're using the correct command from Prerequisites section above

**"Only 10-100 rows scraped instead of full list"**
- TradingView limits rows for non-logged-in users
- **Solution:** Log in to TradingView in your Chrome session:
  1. Keep Chrome running (with remote debugging enabled)
  2. Navigate to TradingView and log in
  3. Run scraper again - it will use your logged-in session
  4. Login persists in `remote-profile/Profile 2` for future runs!

**"Timeout waiting for table to load"**
- Page may require login - see above
- Network may be slow - page will timeout after 20 seconds
- Try refreshing the TradingView page manually in Chrome

**"No constituents extracted"**
- Table structure may have changed - check TradingView page manually
- Try scrolling more with `--max-scrolls 20`
- Use `--debug` flag to save HTML for inspection

### Notes

- **Login Persistence:** Your TradingView login is saved in `remote-profile/Profile 2`, so you only need to log in once
- **Load More Button:** The scraper automatically clicks the "Load More" button (typically 5 clicks for S&P 500) to load all constituents in batches
- **Virtual Scrolling:** After clicking "Load More", TradingView uses virtual scrolling where only ~100 rows are rendered at a time. The scraper tracks unique tickers across scroll positions to ensure complete coverage
- **Dynamic Content:** The scraper waits for dynamic content to load before extracting data
- **Progressive Extraction:** Combines "Load More" clicking with scrolling to collect all unique tickers
- **Sector Extraction:** Sector/industry extraction is best-effort based on TradingView's table structure
- **Session Management:** Chrome must stay open during scraping since we connect to your existing session
- **Non-Destructive:** The scraper doesn't close your Chrome window when finished

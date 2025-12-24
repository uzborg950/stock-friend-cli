# Stock Friend CLI

A Python-based command-line interface tool for European retail investors seeking halal-compliant, momentum-based investment opportunities.

## Overview

Stock Friend CLI provides an interactive terminal interface for:
- **Stock Screening**: Screen entire exchanges, market sectors, or ETF holdings against investment strategies
- **Strategy Management**: Create, edit, and manage custom investment strategies
- **Portfolio Management**: Track holdings, check strategy compliance, and monitor performance

This is a **presentation layer prototype** with mock data for user validation testing. No database integration or external API calls are implemented yet.

## Features

### Current Implementation (v0.1.0)

✅ **Interactive CLI with Rich UI**
- Beautiful terminal interface with Rich library
- Color-coded tables and panels
- Progress indicators and status messages

✅ **Mock Data Demonstration**
- Realistic stock screening results
- Sample investment strategies (Default Momentum, Conservative Growth, Aggressive Tech)
- Example portfolios with holdings and performance metrics

✅ **Complete UI Workflows**
- Stock screening with universe and strategy selection
- Strategy creation wizard with indicator selection
- Portfolio management with holdings tracking

✅ **Comprehensive Testing**
- 93 unit tests covering all CLI components
- >80% code coverage
- Pytest with mocking for isolated testing

## Requirements

- Python 3.12+
- Poetry (for dependency management)
- Conda environment named `stock` (recommended)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd stock-friend-cli
```

### 2. Activate Conda Environment (Recommended)

```bash
conda activate stock
```

### 3. Install Dependencies

```bash
# Install Poetry if not already installed
pip install poetry

# Install project dependencies
poetry install
```

## Usage

### Interactive Mode (Recommended)

Launch the interactive menu-driven interface:

```bash
# Using Poetry
poetry run python -m stock_friend

# Or if installed in environment
python -m stock_friend
```

### CLI Commands

#### Quick Screening

Run a screening operation without interactive menu:

```bash
poetry run python -m stock_friend screen --universe "S&P 500" --strategy 1
```

Options:
- `--universe` / `-u`: Screening universe (default: "SP500")
- `--strategy` / `-s`: Strategy ID (default: "1")

#### Version Information

Display application version:

```bash
poetry run python -m stock_friend version
```

## Testing

### Run All Tests

```bash
# Run all unit tests
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage report
poetry run pytest --cov=src/stock_friend --cov-report=term-missing --cov-report=html
```

### Run Specific Test Modules

```bash
# Test mock data
poetry run pytest tests/unit/cli/test_mock_data.py -v

# Test menu system
poetry run pytest tests/unit/cli/test_menu.py -v

# Test screening CLI
poetry run pytest tests/unit/cli/test_screening_cli.py -v

# Test strategy management
poetry run pytest tests/unit/cli/test_strategy_cli.py -v

# Test portfolio management
poetry run pytest tests/unit/cli/test_portfolio_cli.py -v

# Test main application
poetry run pytest tests/unit/cli/test_app.py -v
```

### Coverage Report

After running tests with coverage, open the HTML report:

```bash
open htmlcov/index.html
```

## Project Structure

```
stock-friend-cli/
├── src/
│   └── stock_friend/
│       ├── __init__.py
│       ├── __main__.py              # Entry point
│       └── cli/
│           ├── __init__.py
│           ├── app.py               # Main Typer application
│           ├── menu.py              # Interactive menu system
│           ├── mock_data.py         # Mock data for demonstration
│           ├── screening_cli.py     # Stock screening interface
│           ├── strategy_cli.py      # Strategy management interface
│           └── portfolio_cli.py     # Portfolio management interface
├── tests/
│   └── unit/
│       └── cli/
│           ├── test_mock_data.py
│           ├── test_menu.py
│           ├── test_screening_cli.py
│           ├── test_strategy_cli.py
│           ├── test_portfolio_cli.py
│           └── test_app.py
├── pyproject.toml                   # Poetry dependencies
├── README.md                        # This file
├── PRD.md                           # Product requirements
├── CLAUDE.md                        # Development guidelines
└── docs/                            # Technical requirements (TRD)
```

## Development

### Code Quality

The project follows strict Python best practices:

- **PEP 8** style guidelines
- **Type hints** throughout
- **SOLID principles** (Single Responsibility, Dependency Inversion)
- **DRY** (Don't Repeat Yourself)
- Clean, self-documenting code with minimal but effective docstrings

### Linting and Formatting

```bash
# Check code style with Ruff
poetry run ruff check src/ tests/

# Type checking with MyPy
poetry run mypy src/
```

## Mock Data

The application currently uses mock data for demonstration:

### Available Universes
- S&P 500
- NASDAQ 100
- Russell 2000
- Dow Jones Industrial
- Custom List

### Sample Strategies
1. **Default Momentum Strategy**: MCDX >= BUY + B-XTrender = GREEN
2. **Conservative Growth**: MCDX = STRONG_BUY + Price > SMA(200)
3. **Aggressive Tech Play**: MCDX = STRONG_BUY + B-XTrender = GREEN + High Volume

### Mock Stock Data
- 10 sample stocks (AAPL, MSFT, GOOGL, NVDA, META, TSLA, AMD, ADBE, CRM, ORCL)
- Includes price, MCDX signals, B-XTrender status, halal compliance
- Volume and market cap information

### Sample Portfolios
1. **Growth Portfolio**: Tech leaders (AAPL, MSFT, NVDA)
2. **Conservative Income**: Stable performers (GOOGL, ADBE)

## Next Steps (Not Yet Implemented)

The following features are planned but NOT currently implemented:

❌ SQLite database integration
❌ Real data fetching from Yahoo Finance API
❌ Halal compliance checking (Zoya/Musaffa APIs)
❌ Technical indicator calculations (MCDX, B-XTrender, SMA)
❌ Strategy evaluation engine
❌ Portfolio performance tracking
❌ CSV export functionality
❌ Caching layer
❌ Rate limiting and error handling

See `docs/TRD_Part5_Implementation_Testing.md` for the complete implementation roadmap.

## Architecture

This application implements a **layered architecture**:

1. **Presentation Layer (CLI)** - ✅ Current implementation
   - Interactive menu system (Questionary)
   - Rich terminal UI (Rich)
   - Command-line interface (Typer)

2. **Application Layer** - ❌ Not yet implemented
   - Service orchestration
   - Use case handlers

3. **Business Logic Layer** - ❌ Not yet implemented
   - Strategy evaluation
   - Indicator calculations
   - Portfolio analysis

4. **Data Access Layer** - ❌ Not yet implemented
   - Repository pattern
   - Gateway abstractions

5. **Infrastructure Layer** - ❌ Not yet implemented
   - Database (SQLite)
   - External APIs (Yahoo Finance, Zoya, Musaffa)
   - Caching

For complete architectural documentation, see `docs/TRD_Part1_Architecture.md`.

## Contributing

This project follows clean code principles. When contributing:

1. **Write tests first** (TDD approach)
2. **Follow SOLID principles**
3. **Use type hints** throughout
4. **Write self-documenting code** with minimal comments
5. **Ensure >80% test coverage**

See `CLAUDE.md` for detailed development guidelines.

## License

[Specify license here]

## Contact

[Specify contact information here]

---

**Note**: This is a prototype implementation focusing on the CLI presentation layer. Mock data is used throughout for user validation testing. No real stock data or halal compliance checking is performed in this version.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start for Agents

**⚠️ IMPORTANT: Choose your development environment:**

**Option 1 - Local Development (Faster iteration):**
```bash
conda activate stock
```

**Option 2 - Docker Development (Production-like environment):**
```bash
docker-compose build
docker-compose run --rm app bash
```

**Recommended Approach:** Use **conda for local development** and **Docker for integration testing/deployment**.

**Key Documentation:**
- Complete Technical Requirements: `docs/TRD_Part1_Architecture.md` through `docs/TRD_Part5_Implementation_Testing.md`
- Product Requirements: `PRD.md`
- This file contains development setup and coding standards

## Project Overview

**stock-friend-cli** is a Python-based command-line interface tool designed for European retail investors seeking halal-compliant, momentum-based investment opportunities.

The system automates stock discovery and technical analysis by screening entire exchanges, market sectors, or ETF holdings against user-defined investment strategies while enforcing strict ethical (halal) and regulatory (EU/UCITS) compliance.

**Key Features:**
- Stock screening across exchanges (S&P 500, NASDAQ, Russell 2000), sectors, market caps, ETF holdings
- Halal compliance filtering with zero false negatives guarantee
- Pluggable investment strategy system with technical indicators (MCDX, B-XTrender, SMA)
- Portfolio management with strategy validation
- Multi-source data integration (Yahoo Finance, halal screening APIs)

## Development Setup

### Python Environment

This project uses a **conda environment** for dependency management.

**Environment Name:** `stock`
**Python Version:** 3.12 (minimum 3.11+ required)

#### Activating the Environment

Before working on this project, agents and developers MUST activate the conda environment:

```bash
conda activate stock
```

#### Environment Details

- The `stock` conda environment is configured with Python 3.12
- This environment should be activated for all development tasks including:
  - Running the CLI application
  - Installing dependencies
  - Running tests
  - Executing any Python scripts

#### Verifying the Environment

To verify you're in the correct environment:

```bash
# Check Python version (should be 3.12.x)
python --version

# Check active conda environment (should show 'stock')
conda info --envs | grep '*'
```

#### Installing Dependencies

Once the environment is activated, install project dependencies using Poetry:

```bash
# Install Poetry if not available
pip install poetry

# Install project dependencies
poetry install
```

For detailed dependency specifications, see `docs/TRD_Part5_Implementation_Testing.md`.

### Docker Development Environment

**⚠️ IMPORTANT: This project uses Docker containers for development to ensure portability and simplified deployment.**

#### Why Docker?

We use Docker containers for:

1. **Portability:** Consistent development environment across all platforms (Windows, macOS, Linux)
2. **Simplified Deployment:** Same container used in development, testing, and production
3. **Dependency Isolation:** Eliminates "works on my machine" problems
4. **Easy Onboarding:** New developers can start immediately without complex setup
5. **CI/CD Integration:** Seamless integration with automated testing and deployment pipelines

#### Docker Setup

**Prerequisites:**
- Docker Desktop installed and running
- Docker Compose installed (included with Docker Desktop)

#### Development Workflow

**Option 1: Docker for Development (Recommended for Production-like Environment)**

```bash
# Build the Docker image
docker-compose build

# Run the application in Docker container
docker-compose up

# Run CLI commands in container
docker-compose run --rm app python -m stock_cli screen --exchange SP500

# Run tests in container
docker-compose run --rm app pytest

# Access container shell for debugging
docker-compose run --rm app bash
```

**Option 2: Local Development with Conda (Recommended for Active Development)**

```bash
# Use conda environment for faster iteration during development
conda activate stock
python -m stock_cli screen --exchange SP500

# Test locally
pytest

# Build Docker image for testing deployment
docker-compose build
docker-compose up
```

#### Docker Configuration Files

The project includes the following Docker configuration:

- **`Dockerfile`**: Multi-stage build optimized for Python 3.12
  - Stage 1: Build dependencies and install Poetry
  - Stage 2: Production runtime with minimal image size
  - Security: Non-root user, minimal attack surface

- **`docker-compose.yml`**: Development and deployment orchestration
  - Service definitions for the CLI application
  - Volume mounts for local development
  - Environment variable configuration
  - Network configuration for external API access

- **`.dockerignore`**: Excludes unnecessary files from Docker build context
  - Python cache files, test files, documentation
  - Reduces build time and image size

#### Docker Best Practices for This Project

1. **Development:** Use conda environment for rapid iteration and debugging
2. **Testing:** Run full test suite in Docker container before committing
3. **Deployment:** Always deploy using Docker images
4. **Debugging:** Use `docker-compose run --rm app bash` to access container shell
5. **Logs:** Access container logs with `docker-compose logs -f`

#### Docker Image Structure

```
Base Image: python:3.12-slim
├── System dependencies (build essentials, SQLite)
├── Poetry installation
├── Application dependencies (from pyproject.toml)
├── Application source code (src/)
├── Static data files (data/universes/)
└── Configuration files (config/)

Working Directory: /app
User: nonroot (UID 1000)
```

#### Environment Variables in Docker

The Docker container expects environment variables to be configured in a `.env` file:

```bash
# API Keys (encrypted at rest)
YAHOO_FINANCE_API_KEY=your_key_here
ZOYA_API_KEY=your_key_here
MUSAFFA_API_KEY=your_key_here

# Database Configuration
DATABASE_PATH=/app/data/stock_cli.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/app/logs/stock-cli.log

# Cache Configuration
CACHE_TTL_HOURS=24
CACHE_MAX_SIZE_MB=500
```

**Security Note:** Never commit `.env` file to version control. Use `.env.example` as a template.

#### Hybrid Development Approach

**Recommended workflow combines both conda and Docker:**

1. **Local Development (Conda):**
   - Fast feedback loop for code changes
   - Easy debugging with IDE integration
   - Quick test execution
   ```bash
   conda activate stock
   pytest tests/unit/
   ```

2. **Integration Testing (Docker):**
   - Test in production-like environment
   - Validate deployment configuration
   - Run full integration test suite
   ```bash
   docker-compose run --rm app pytest tests/integration/
   ```

3. **Deployment (Docker):**
   - Deploy containerized application
   - Consistent runtime environment
   - Easy scaling and orchestration

#### Docker Performance Considerations

- **Build time:** ~3-5 minutes for fresh build (cached builds ~30 seconds)
- **Image size:** ~450 MB (optimized with multi-stage builds)
- **Startup time:** ~2 seconds for CLI commands
- **Volume mounts:** Use for development to avoid rebuilds on code changes

For detailed Docker specifications and deployment architecture, see `docs/TRD_Part5_Implementation_Testing.md`.

## Architecture

The complete system architecture, design patterns, and technical specifications are documented in the Technical Requirements Document (TRD) located in the `docs/` directory:

- **Part 1:** Architecture & Foundation (`docs/TRD_Part1_Architecture.md`)
  - System architecture layers (Presentation, Application, Business Logic, Data Access, Infrastructure)
  - Data flow diagrams and sequence diagrams
  - Design patterns: Strategy, Factory, Repository, Dependency Injection
  - SOLID principles with concrete examples

- **Part 2:** Data Models & Service Layer (`docs/TRD_Part2_DataModels_Services.md`)
  - Domain models and dataclasses
  - SQLite database schema with ER diagram
  - Service interfaces: ScreeningService, StrategyService

- **Part 3:** Indicator Architecture & Data Access (`docs/TRD_Part3_Indicators_DataAccess.md`)
  - IIndicator interface and indicator implementations (MCDX, B-XTrender, SMA)
  - PortfolioService implementation
  - Gateway abstractions for external APIs

- **Part 4:** Integration, Security & Performance (`docs/TRD_Part4_Integration_Security_Performance.md`)
  - API gateway implementations (Yahoo Finance, Zoya/Musaffa, Universe providers)
  - Caching strategy (L1: memory, L2: SQLite)
  - Rate limiting and circuit breaker patterns
  - Security architecture with encryption

- **Part 5:** Implementation & Testing Strategy (`docs/TRD_Part5_Implementation_Testing.md`)
  - MVP feature breakdown and 7-week roadmap
  - Project directory structure
  - Development guidelines
  - Testing strategy

### Key Architectural Principles

1. **Layer Separation:** Clear boundaries between CLI, services, business logic, and data access
2. **Dependency Inversion:** Services depend on gateway abstractions, not concrete implementations
3. **Pluggable Indicators:** New indicators can be added without modifying core engine
4. **Fail-Safe Halal Filtering:** Zero false negatives guarantee for compliance

## Testing

### Testing Strategy

The project follows a **test pyramid** approach with 80% minimum code coverage:

- **70% Unit Tests:** Test individual components in isolation with mocked dependencies
- **20% Integration Tests:** Test service layer with real database and mocked external APIs
- **10% End-to-End Tests:** Test complete workflows with deterministic mock data

### Running Tests

**Local Testing (Conda - Faster for unit tests):**

```bash
# Activate environment first
conda activate stock

# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_indicators.py

# Run with verbose output
pytest -v

# Run performance tests
pytest tests/performance/ --benchmark-only
```

**Docker Testing (Recommended for integration tests):**

```bash
# Run all tests in Docker container
docker-compose run --rm app pytest

# Run with coverage report
docker-compose run --rm app pytest --cov=src --cov-report=html --cov-report=term

# Run integration tests specifically
docker-compose run --rm app pytest tests/integration/

# Run performance benchmarks
docker-compose run --rm app pytest tests/performance/ --benchmark-only
```

**CI/CD Testing:**

In continuous integration pipelines, always use Docker for consistent test results:

```bash
docker-compose build
docker-compose run --rm app pytest --cov=src --cov-report=xml
```

### Test Organization

```
tests/
├── unit/              # Unit tests (fast, isolated)
│   ├── test_indicators.py
│   ├── test_services.py
│   └── test_gateways.py
├── integration/       # Integration tests (database, API mocks)
│   ├── test_screening_flow.py
│   └── test_portfolio_flow.py
├── performance/       # Performance benchmarks
│   └── test_indicator_performance.py
└── fixtures/          # Shared test data and fixtures
    ├── sample_data.py
    └── mock_responses.py
```

### Testing Requirements

- All new features MUST include unit tests
- Integration tests required for service-layer changes
- Performance tests for indicator calculations (<0.5s per stock for MCDX)
- Mock external APIs using `pytest-mock` and `responses` library

For complete testing specifications, see `docs/TRD_Part5_Implementation_Testing.md`.

## Notes

### Project Configuration

- This is a Python project (based on .gitignore configuration)
- The project uses standard Python .gitignore patterns supporting various package managers (pip, poetry, uv, pdm, pixi)
- Environment variables should be stored in `.env` files (gitignored)

### Docker Configuration Files

The following Docker files should be created in the project root:

- **`Dockerfile`**: Multi-stage build for Python 3.12 application
- **`docker-compose.yml`**: Orchestration for development and deployment
- **`.dockerignore`**: Exclude unnecessary files from Docker build context
- **`.env.example`**: Template for environment variables (committed to repo)
- **`.env`**: Actual environment variables with API keys (NEVER commit)

### Development Environment Summary

| Environment | Use Case | Activation | Speed | Use For |
|-------------|----------|------------|-------|---------|
| **Conda (`stock`)** | Local development | `conda activate stock` | Fast | Active coding, debugging, unit tests |
| **Docker** | Integration testing, deployment | `docker-compose run --rm app bash` | Slower | Integration tests, production simulation, deployment |

### Recommended Workflow

1. **Active Development:** Use conda environment for fast iteration
2. **Before Commit:** Run full test suite in Docker to ensure consistency
3. **CI/CD:** Always use Docker for automated testing and deployment
4. **Production:** Deploy Docker containers only

### Clean Code Persona
Act as a Senior Clean Code Architect. Your goal is to write and refactor code that is production-ready, maintainable, and human-readable.

**Strictly adhere to the following directives:**

- **SOLID Principles**: Ensure classes/functions have a single responsibility and dependencies are abstracted.

- **DRY (Don't Repeat Yourself)**: Abstract repetitive logic into reusable utility functions or classes.

- **Readability First**: Use verbose, semantic variable names. Prefer Guard Clauses over nested if/else. Avoid magic numbers.

- **Self-Documenting**: The code structure should explain the what; comments should only explain the why. Resist writing line comments that can be easily understood by the code. Function level docstring should be minimal but effective without redundancy.

If you refactor existing code, briefly list the specific principles (e.g., 'Applied SRP', 'Removed Magic Numbers') used to improve it.

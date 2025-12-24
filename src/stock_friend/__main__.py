"""Entry point for Stock Friend CLI application."""

from stock_friend.cli.app import app


def main() -> None:
    """Main entry point for the application."""
    app()


if __name__ == "__main__":
    main()

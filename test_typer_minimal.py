#!/usr/bin/env python
"""Minimal test to debug Typer issue."""

from typing import Annotated
import typer

app = typer.Typer()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Main callback."""
    if ctx.invoked_subcommand is not None:
        return
    print("Interactive menu would run here")

@app.command()
def screen(
    universe: str = typer.Option(default="SP500", help="Screening universe"),
    strategy: str = typer.Option(default="1", help="Strategy ID"),
) -> None:
    """Test screen command."""
    print(f"Universe: {universe}, Strategy: {strategy}")

if __name__ == "__main__":
    app()

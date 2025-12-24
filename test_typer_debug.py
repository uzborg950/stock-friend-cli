"""Debug script to test Typer option parsing."""
import typer

app = typer.Typer()


@app.command()
def test_cmd(
    universe: str = typer.Option("default", help="Test universe"),
    strategy: str = typer.Option("1", help="Test strategy"),
) -> None:
    """Test command with options."""
    print(f"Universe: {universe}")
    print(f"Strategy: {strategy}")


if __name__ == "__main__":
    app()

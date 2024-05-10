"""Command-line interface."""

import click


@click.command()
@click.version_option()
def main() -> None:
    """Scripts."""


if __name__ == "__main__":
    main(prog_name="scripts")  # pragma: no cover

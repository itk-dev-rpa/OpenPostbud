"""Entry point for the CLI."""

import argparse

from OpenPostbud.middleware import authentication


# pylint: disable=unused-argument
def admin_access_command(args: argparse.Namespace):
    """The command to run on the 'admin_access' subcommand."""
    authentication.grant_admin_access()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="OpenPostbud",
        description="OpenPostbud is a web app used to do mass sending of Digital Post using SF1601."
    )

    subparsers = parser.add_subparsers(title="Subcommands", required=True)

    admin_parser = subparsers.add_parser("admin_access", help="Generate a single-use admin URL to the web app.")
    admin_parser.set_defaults(func=admin_access_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

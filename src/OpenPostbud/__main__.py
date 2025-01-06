

import argparse

from OpenPostbud.middleware import authentication
import OpenPostbud.main


def admin_access_command(args: argparse.Namespace):
    authentication.grant_admin_access()


def run_command(args: argparse.Namespace):
    OpenPostbud.main.main(reload=False)


def main():
    parser = argparse.ArgumentParser(
        prog="OpenPostbud",
        description="OpenPostbud is a web app used to do mass sending of Digital Post using SF1601."
    )

    subparsers = parser.add_subparsers(title="Subcommands", required=True)

    admin_parser = subparsers.add_parser("admin_access", help="Use this command to get a single-use admin URL to the web app.")
    admin_parser.set_defaults(func=admin_access_command)

    run_parser = subparsers.add_parser("run", help="Run the web application.")
    run_parser.set_defaults(func=run_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

"""Entry point for the CLI."""

import argparse

from OpenPostbud.middleware import authentication
import OpenPostbud.main
from OpenPostbud.workers import registration_worker, shipment_worker


# pylint: disable=unused-argument
def admin_access_command(args: argparse.Namespace):
    """The command to run on the 'admin_access' subcommand."""
    authentication.grant_admin_access()


# pylint: disable=unused-argument
def run_command(args: argparse.Namespace):
    """The command to run on the 'run' subcommand."""
    OpenPostbud.main.main(reload=False)


# pylint: disable=unused-argument
def r_worker_command(args: argparse.Namespace):
    """The command to run on the 'registration_worker' subcommand."""
    registration_worker.start_process()


# pylint: disable=unused-argument
def s_worker_command(args: argparse.Namespace):
    """The command to run on the 'shipment_worker' subcommand."""
    shipment_worker.start_process()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="OpenPostbud",
        description="OpenPostbud is a web app used to do mass sending of Digital Post using SF1601."
    )

    subparsers = parser.add_subparsers(title="Subcommands", required=True)

    admin_parser = subparsers.add_parser("admin_access", help="Generate a single-use admin URL to the web app.")
    admin_parser.set_defaults(func=admin_access_command)

    run_parser = subparsers.add_parser("run", help="Run the web application.")
    run_parser.set_defaults(func=run_command)

    r_worker_parser = subparsers.add_parser("registration_worker", help="Start the registration worker.")
    r_worker_parser.set_defaults(func=r_worker_command)

    s_worker_parser = subparsers.add_parser("shipment_worker", help="Start the shipment worker.")
    s_worker_parser.set_defaults(func=s_worker_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

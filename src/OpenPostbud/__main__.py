"""Entry point for the CLI."""

import argparse

from OpenPostbud.database.check_registration import registration_job
from OpenPostbud.database.digital_post import shipments
from OpenPostbud.database.nemsms import nemsms_shipments
from OpenPostbud.middleware import authentication
from OpenPostbud.database import connection



def admin_access_command(*_):
    """The function to run on the 'admin_access' subcommand."""
    authentication.grant_admin_access()


def database_cleanup(*_):
    """The function to run on the 'database_cleanup' subcommand."""
    shipments.delete_old_shipments()
    registration_job.delete_old_registration_jobs()
    nemsms_shipments.delete_old_shipments()


def create_database(*_):
    """The function to run on the 'create_database' subcommand."""
    connection.create_tables()


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="OpenPostbud",
        description="OpenPostbud is a web app used to do mass sending of Digital Post using SF1601."
    )

    subparsers = parser.add_subparsers(title="Subcommands", required=True)

    admin_parser = subparsers.add_parser("admin_access", help="Generate a single-use admin URL to the web app.")
    admin_parser.set_defaults(func=admin_access_command)

    cleanup_parser = subparsers.add_parser("database_cleanup", help="Delete all objects in the database that are past their deletion date.")
    cleanup_parser.set_defaults(func=database_cleanup)

    create_db_parser = subparsers.add_parser("create_database", help="Create a new database with all needed tables.")
    create_db_parser.set_defaults(func=create_database)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()

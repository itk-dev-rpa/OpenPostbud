"""Test package for OpenPostbud.

Tests in this package exercise the database layer without running the web app.
They must be run from the repository root so that the cwd-relative ``.env`` file
and the migration SQL folder resolve correctly:

    python -m unittest discover -s tests -t . -v
"""

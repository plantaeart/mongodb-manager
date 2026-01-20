#!/usr/bin/env python3
"""MongoDB Manager - CLI Entry Point

This is the main entry point for the MongoDB Manager application.
It provides a CLI for managing MongoDB backups and restores using mongodump/mongorestore.
"""

from app.core.cli import app


def main():
    """Main entry point for the CLI application"""
    app()


if __name__ == "__main__":
    main()

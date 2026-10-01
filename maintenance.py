from __future__ import annotations

import argparse

from app import create_app
from services.maintenance_service import cleanup_expired_jobs


def main():
    parser = argparse.ArgumentParser(description="AvatarForge AI maintenance utilities")
    parser.add_argument("command", choices=["cleanup-jobs"])
    parser.add_argument("--older-than-hours", type=int, default=None)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if args.command == "cleanup-jobs":
            print(cleanup_expired_jobs(older_than_hours=args.older_than_hours))


if __name__ == "__main__":
    main()

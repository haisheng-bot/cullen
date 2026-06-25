"""Create OpenStock AI database tables.

Usage:
    python3 scripts/init_db.py

Reads DATABASE_URL from the environment (or .env). Safe to run repeatedly;
existing tables are left untouched.
"""
from __future__ import annotations

from packages.config import get_settings
from packages.db.models import Base
from packages.db.session import get_engine


def main() -> None:
    settings = get_settings()
    engine = get_engine()
    Base.metadata.create_all(engine)
    print(f"OpenStock AI tables ready at: {settings.database_url}")
    print(f"Created/verified tables: {sorted(Base.metadata.tables.keys())}")


if __name__ == "__main__":
    main()

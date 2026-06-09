"""Migrate existing schedules to use the new /scheduled-run/{agent_id} endpoint.

Old schedules point to /agents/{agent_id}/runs (Agno default).
New schedules should point to /scheduled-run/{agent_id} so the output
gets forwarded to WhatsApp.

Run: python -m scripts.migrate_schedules
"""

import json
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set in .env")
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("ERROR: psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

# The table name Agno uses for schedules (in the 'ai' schema by default)
DB_SCHEMA = "ai"
SCHEDULES_TABLE = "agno_schedules"
QUALIFIED_TABLE = f'"{DB_SCHEMA}"."{SCHEDULES_TABLE}"'

# Pattern matching old-style run endpoints
OLD_ENDPOINT_RE = re.compile(r"^/agents/([^/]+)/runs/?$")


def migrate():
    # Strip SQLAlchemy dialect prefix (e.g. postgresql+psycopg2:// -> postgresql://)
    db_url = re.sub(r"^postgresql\+\w+://", "postgresql://", DATABASE_URL)
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        # List all schedules
        cur.execute(f"SELECT id, name, endpoint, payload FROM {QUALIFIED_TABLE}")
        rows = cur.fetchall()

        if not rows:
            print("No schedules found.")
            return

        updated = 0
        for schedule_id, name, endpoint, payload in rows:
            match = OLD_ENDPOINT_RE.match(endpoint or "")
            if not match:
                print(f"  SKIP: {name} (endpoint={endpoint}) — already using custom endpoint")
                continue

            agent_id = match.group(1)
            new_endpoint = f"/scheduled-run/{agent_id}"

            # Parse payload and ensure user_id is present
            payload_dict = payload if isinstance(payload, dict) else json.loads(payload or "{}")

            print(f"  UPDATE: {name}")
            print(f"    endpoint: {endpoint} -> {new_endpoint}")
            print(f"    payload: {json.dumps(payload_dict)}")

            cur.execute(
                f"UPDATE {QUALIFIED_TABLE} SET endpoint = %s WHERE id = %s",
                (new_endpoint, schedule_id),
            )
            updated += 1

        if updated:
            conn.commit()
            print(f"\nMigrated {updated} schedule(s) to use /scheduled-run/ endpoint.")
            print("NOTE: Make sure each schedule's payload includes a 'user_id' field")
            print("with the phone number, otherwise the agent will fall back to the")
            print("registered phone number for that agent.")
        else:
            print("\nNo schedules needed migration.")

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    migrate()

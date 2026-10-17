from contextlib import closing
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "precious_metals.db"


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    source TEXT NOT NULL,
                    series TEXT NOT NULL,
                    observation_date TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (source, series, observation_date)
                )
            """)


def save_observations(
    source,
    series,
    observations,
    date_key="date",
    value_key="value",
    unit="",
):
    rows = []

    for observation in observations:
        raw_value = observation[value_key]

        # FRED uses "." to mean that an observation is unavailable.
        if raw_value == "." or raw_value is None:
            continue

        rows.append((
            source,
            series,
            str(observation[date_key])[:10],
            float(raw_value),
            unit,
        ))

    if not rows:
        return 0

    init_db()
    with closing(sqlite3.connect(DB_PATH)) as connection:
        with connection:
            connection.executemany("""
                INSERT INTO observations
                    (source, series, observation_date, value, unit)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (source, series, observation_date)
                DO UPDATE SET
                    value = excluded.value,
                    unit = excluded.unit
            """, rows)
    return len(rows)


def get_observations(limit=500):
    init_db()
    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT source, series, observation_date, value, unit
            FROM observations
            ORDER BY observation_date DESC, source, series
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_observation_count():
    init_db()
    with closing(sqlite3.connect(DB_PATH)) as connection:
        row = connection.execute(
            "SELECT COUNT(*) FROM observations"
        ).fetchone()
    return row[0]
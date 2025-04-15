import asyncio
import sqlite3
from pathlib import Path

CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR / "data"


async def system_database(sql_query: str, **kwargs):
    """Execute SQL query on the ship database and return the results.

    Args:
        sql_query: The SQL query to execute.

    Returns:
        Dict containing success status, results (if any), and message.
    """
    db_path = DATA_DIR / "ship_database.sqlite"

    if not db_path.exists():
        return {
            "success": False,
            "message": "Database not found. Please run the seed script first.",
            "results": None,
        }

    try:
        # Run SQLite operation in a thread pool to avoid blocking the event loop
        return await asyncio.to_thread(_execute_query, db_path, sql_query)
    except Exception as e:
        return {
            "success": False,
            "message": f"Error executing query: {str(e)}",
            "results": None,
        }


def _execute_query(db_path, sql_query):
    """Helper function to execute SQL queries synchronously.

    Args:
        db_path: Path to the SQLite database.
        sql_query: The SQL query to execute.

    Returns:
        Dict containing results and metadata.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name

    try:
        cursor = conn.cursor()
        cursor.execute(sql_query)

        # Check if this is a SELECT query (has results to fetch)
        if sql_query.strip().lower().startswith("select"):
            results = [dict(row) for row in cursor.fetchall()]
            return {
                "success": True,
                "message": f"Query executed successfully. Returned {len(results)} rows.",
                "results": results,
                "column_names": (
                    [desc[0] for desc in cursor.description]
                    if cursor.description
                    else []
                ),
            }
        else:
            # For non-SELECT queries (INSERT, UPDATE, DELETE)
            conn.commit()
            return {
                "success": True,
                "message": f"Query executed successfully. Rows affected: {cursor.rowcount}",
                "results": None,
            }
    except sqlite3.Error as e:
        return {"success": False, "message": f"SQLite error: {str(e)}", "results": None}
    finally:
        conn.close()

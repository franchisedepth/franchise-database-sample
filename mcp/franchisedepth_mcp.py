"""FranchiseDepth FDD Database: read-only MCP server.

Connects franchisedepth.sqlite to Claude Desktop, Cursor and other MCP clients. The database is
opened read-only, and an SQLite authorizer allows only reads, so no tool can change it.

  uv run --with mcp python franchisedepth_mcp.py [path/to/franchisedepth.sqlite]

With no path, it looks for franchisedepth.sqlite one folder up (the product's root folder).
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

try:  # mcp 2.x renamed FastMCP to MCPServer; same name/instructions/tool()/run() interface
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP

HERE = Path(__file__).resolve().parent
DB = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "franchisedepth.sqlite"
GUIDE = DB.parent / "AGENTS.md"
MAX_ROWS = 500
READ_ONLY_ACTIONS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION,
                     getattr(sqlite3, "SQLITE_RECURSIVE", 33)}

mcp = FastMCP("franchisedepth", instructions=(
    "FranchiseDepth FDD Database: fees, investment, Item 19 earnings, Item 20 outlets and closures, "
    "state counts and agreement terms for US franchise brands, from their Franchise Disclosure Documents. "
    "Call guide() first: it explains every table, the units, NULLs and methods. Join tables on brand_slug. "
    "Cite the brand's fdd_year and, for Item 19 figures, the cohort and fdd_page."))


def _conn() -> sqlite3.Connection:
    if not DB.exists():
        raise FileNotFoundError(f"database not found: {DB}")
    c = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    c.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in READ_ONLY_ACTIONS else sqlite3.SQLITE_DENY)
    return c


def _rows(sql: str, args: tuple = (), limit: int = MAX_ROWS) -> list[dict]:
    with _conn() as c:
        cur = c.execute(sql, args)
        return [dict(r) for r in cur.fetchmany(min(max(1, limit), MAX_ROWS))]


@mcp.tool()
def guide() -> str:
    """The database guide (AGENTS.md): every table and column, units, what NULL means, and how derived figures are computed. Read it before querying."""
    return GUIDE.read_text(encoding="utf-8") if GUIDE.exists() else "AGENTS.md not found next to the database."


@mcp.tool()
def list_tables() -> list[dict]:
    """Every table with its description and row count, plus the views."""
    tables = _rows("SELECT table_name, description, row_count FROM table_docs ORDER BY table_name")
    views = _rows("SELECT name FROM sqlite_master WHERE type = 'view' ORDER BY name")
    return tables + [{"table_name": v["name"], "description": "view", "row_count": None} for v in views]


@mcp.tool()
def describe_table(table: str) -> list[dict]:
    """Columns of one table with type and meaning."""
    return _rows("SELECT column_name, type, description FROM column_docs WHERE table_name = ? ", (table,))


@mcp.tool()
def query(sql: str, limit: int = 200) -> dict:
    """Run one read-only SQL SELECT and return up to `limit` rows (max 500). Join tables on brand_slug."""
    try:
        rows = _rows(sql.strip().rstrip(";"), (), limit)
        return {"rows": rows, "row_count": len(rows), "truncated_at": min(max(1, limit), MAX_ROWS)}
    except sqlite3.Error as e:
        return {"error": str(e), "hint": "Only single SELECT statements are allowed. See describe_table() for column names."}


@mcp.tool()
def search_brands(text: str, industry: str | None = None, limit: int = 20) -> list[dict]:
    """Find brands by name (case-insensitive substring), optionally within an industry code prefix."""
    sql = "SELECT brand_slug, brand_name, industry, industry_label, fdd_year FROM brands WHERE brand_name LIKE ?"
    args: list = [f"%{text}%"]
    if industry:
        sql += " AND industry LIKE ?"
        args.append(f"{industry}%")
    return _rows(sql + " ORDER BY brand_name", tuple(args), limit)


@mcp.tool()
def get_brand(brand_slug: str) -> dict:
    """Everything on file for one brand: identity, fees, outlets, closure rate, outlet growth, all-in fee, comparable revenue, Item 19 figures, turnover and closures by year, agreement terms."""
    with _conn() as c:
        have = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    out: dict = {}
    for t in ("brands", "fees", "fee_notes", "brand_metrics", "comparable_revenue", "agreement_terms"):
        if t in have:
            r = _rows(f"SELECT * FROM {t} WHERE brand_slug = ?", (brand_slug,), 1)
            out[t] = r[0] if r else None
    for t, order in (("item19_figures", "metric, cohort"), ("turnover_by_year", "year"), ("closure_by_year", "year"),
                     ("outlets_by_year", "year, outlet_type")):
        if t in have:
            out[t] = _rows(f"SELECT * FROM {t} WHERE brand_slug = ? ORDER BY {order}", (brand_slug,))
    if not out.get("brands"):
        return {"error": f"no brand with slug {brand_slug!r}; use search_brands()"}
    return out


if __name__ == "__main__":
    mcp.run()

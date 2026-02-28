"""
GridTRX MCP Server — structured AI agent interface to the accounting engine.

Wraps models.py functions as MCP tools. Every tool takes db_path as its first
parameter so the agent can work with any database file.

Usage:
    pip install mcp
    python mcp_server.py          # stdio transport (for Claude Desktop / Claude Code)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP
import models

mcp = FastMCP("GridTRX", instructions="Double-entry accounting engine")

_initialized_db = None

def _init(db_path: str):
    """Initialize database connection, only re-init if path changes."""
    global _initialized_db
    if _initialized_db != db_path:
        models.init_db(db_path)
        _initialized_db = db_path


def _row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    if row is None:
        return None
    return dict(row)


def _rows_to_dicts(rows):
    """Convert a list of sqlite3.Row to a list of plain dicts."""
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════
# READ-ONLY TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def list_accounts(db_path: str, query: str = "") -> list[dict]:
    """List all accounts in the chart of accounts. Optionally filter by name/description with query."""
    _init(db_path)
    if query:
        rows = models.search_accounts(query)
    else:
        rows = models.get_accounts()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
            "normal_balance": r["normal_balance"],
            "type": r["account_type"],
        }
        for r in rows
    ]


@mcp.tool()
def get_balance(
    db_path: str,
    account_name: str,
    date_from: str = "",
    date_to: str = "",
) -> dict:
    """Get the balance of a single account, optionally within a date range (YYYY-MM-DD)."""
    _init(db_path)
    acct = models.get_account_by_name(account_name)
    if not acct:
        raise ValueError(f"Account not found: {account_name}")
    raw = models.get_account_balance(
        acct["id"],
        date_from=date_from or None,
        date_to=date_to or None,
    )
    sign = 1 if acct["normal_balance"] == "D" else -1
    balance = raw * sign
    return {
        "account": acct["name"],
        "balance_cents": balance,
        "formatted": models.fmt_amount(balance),
    }


@mcp.tool()
def get_ledger(
    db_path: str,
    account_name: str,
    date_from: str = "",
    date_to: str = "",
) -> list[dict]:
    """Get the full ledger for an account with running balance. Optionally filter by date range."""
    _init(db_path)
    acct = models.get_account_by_name(account_name)
    if not acct:
        raise ValueError(f"Account not found: {account_name}")
    entries = models.get_ledger(
        acct["id"],
        date_from=date_from or None,
        date_to=date_to or None,
    )
    return [
        {
            "txn_id": e["txn_id"],
            "date": e["date"],
            "reference": e["reference"],
            "description": e["description"],
            "amount_cents": e["amount"],
            "amount_formatted": models.fmt_amount(e["amount"]),
            "running_balance_cents": e["running_balance"],
            "running_balance_formatted": models.fmt_amount(e["running_balance"]),
            "cross_accounts": e["cross_accounts"],
            "reconciled": bool(e["reconciled"]),
        }
        for e in entries
    ]


@mcp.tool()
def trial_balance(db_path: str, as_of_date: str = "") -> dict:
    """Get the trial balance — all posting accounts with non-zero balances, split into Dr/Cr columns."""
    _init(db_path)
    accounts, total_dr, total_cr = models.get_trial_balance(
        as_of_date=as_of_date or None,
    )
    return {
        "accounts": [
            {
                "name": a["name"],
                "description": a["description"],
                "normal_balance": a["normal_balance"],
                "debit_cents": a["debit"],
                "debit_formatted": models.fmt_amount(a["debit"]) if a["debit"] else "",
                "credit_cents": a["credit"],
                "credit_formatted": models.fmt_amount(a["credit"]) if a["credit"] else "",
            }
            for a in accounts
        ],
        "total_debit_cents": total_dr,
        "total_debit_formatted": models.fmt_amount(total_dr),
        "total_credit_cents": total_cr,
        "total_credit_formatted": models.fmt_amount(total_cr),
    }


@mcp.tool()
def generate_report(
    db_path: str,
    report_name: str,
    date_from: str = "",
    date_to: str = "",
) -> list[dict]:
    """Generate a financial report (BS, IS, AJE, etc.) with computed balances. Returns line items."""
    _init(db_path)
    report = models.find_report_by_name(report_name)
    if not report:
        raise ValueError(f"Report not found: {report_name}")
    items = models.compute_report_column(
        report["id"],
        date_from=date_from or None,
        date_to=date_to or None,
    )
    result = []
    for item_dict, amount in items:
        entry = {
            "description": item_dict.get("description") or item_dict.get("acct_name") or "",
            "item_type": item_dict.get("item_type", ""),
            "indent": item_dict.get("indent", 0),
            "amount_cents": amount,
            "amount_formatted": models.fmt_amount(amount),
        }
        if item_dict.get("acct_name"):
            entry["account_name"] = item_dict["acct_name"]
        if item_dict.get("sep_style"):
            entry["separator_style"] = item_dict["sep_style"]
        result.append(entry)
    return result


@mcp.tool()
def get_transaction(db_path: str, txn_id: int) -> dict:
    """Get a single transaction by ID, including all its journal lines."""
    _init(db_path)
    txn, lines = models.get_transaction(txn_id)
    if not txn:
        raise ValueError(f"Transaction not found: {txn_id}")
    return {
        "id": txn["id"],
        "date": txn["date"],
        "description": txn["description"],
        "reference": txn["reference"],
        "lines": [
            {
                "account_name": l["account_name"],
                "amount_cents": l["amount"],
                "amount_formatted": models.fmt_amount(l["amount"]),
                "description": l["description"],
                "reconciled": bool(l["reconciled"]),
            }
            for l in lines
        ],
    }


@mcp.tool()
def search_transactions(
    db_path: str, query: str, limit: int = 100
) -> list[dict]:
    """Search transactions by description, reference, or account name."""
    _init(db_path)
    rows = models.search_transactions(query, limit=limit)
    return [
        {
            "txn_id": r["txn_id"],
            "date": r["date"],
            "reference": r["reference"],
            "description": r["description"],
            "accounts": r["accounts"],
            "total_amount_cents": r["total_amount"] or 0,
            "total_amount_formatted": models.fmt_amount(r["total_amount"] or 0),
        }
        for r in rows
    ]


@mcp.tool()
def list_reports(db_path: str) -> list[dict]:
    """List all available reports (BS, IS, AJE, etc.)."""
    _init(db_path)
    rows = models.get_reports()
    return [
        {
            "id": r["id"],
            "name": r["name"],
            "description": r["description"],
        }
        for r in rows
    ]


@mcp.tool()
def list_rules(db_path: str) -> list[dict]:
    """List all import rules for CSV auto-categorization."""
    _init(db_path)
    rows = models.get_import_rules()
    return [
        {
            "id": r["id"],
            "keyword": r["keyword"],
            "account": r["account_name"],
            "tax_code": r["tax_code"],
            "priority": r["priority"],
        }
        for r in rows
    ]


@mcp.tool()
def get_info(db_path: str) -> dict:
    """Get company metadata: name, fiscal year end, lock date."""
    _init(db_path)
    return {
        "company_name": models.get_meta("company_name", ""),
        "fiscal_year_end": models.get_meta("fiscal_year_end", ""),
        "lock_date": models.get_meta("lock_date", ""),
    }


# ═══════════════════════════════════════════════════════════════════
# WRITE TOOLS
# ═══════════════════════════════════════════════════════════════════

@mcp.tool()
def post_transaction(
    db_path: str,
    date: str,
    description: str,
    amount: str,
    debit_account: str,
    credit_account: str,
) -> dict:
    """Post a simple 2-line transaction. Amount is in dollars (e.g. '1500.00'). Date is YYYY-MM-DD."""
    _init(db_path)
    dr_acct = models.get_account_by_name(debit_account)
    if not dr_acct:
        raise ValueError(f"Debit account not found: {debit_account}")
    cr_acct = models.get_account_by_name(credit_account)
    if not cr_acct:
        raise ValueError(f"Credit account not found: {credit_account}")
    amount_cents = models.parse_amount(amount)
    if amount_cents <= 0:
        raise ValueError(f"Amount must be positive: {amount}")
    ref = models.generate_ref()
    txn_id = models.add_simple_transaction(
        date, ref, description, dr_acct["id"], cr_acct["id"], amount_cents
    )
    return {"txn_id": txn_id, "reference": ref}


@mcp.tool()
def delete_transaction(db_path: str, txn_id: int) -> dict:
    """Delete a transaction by ID. Respects lock date."""
    _init(db_path)
    models.delete_transaction(txn_id)
    return {"deleted": True, "txn_id": txn_id}


@mcp.tool()
def add_account(
    db_path: str,
    name: str,
    normal_balance: str,
    description: str = "",
) -> dict:
    """Add a new posting account. normal_balance is 'D' (debit-normal) or 'C' (credit-normal)."""
    _init(db_path)
    if normal_balance not in ("D", "C"):
        raise ValueError("normal_balance must be 'D' or 'C'")
    account_id = models.add_account(name, normal_balance, description)
    return {"account_id": account_id, "name": name}


@mcp.tool()
def add_rule(
    db_path: str,
    keyword: str,
    account_name: str,
    tax_code: str = "",
    priority: int = 0,
) -> dict:
    """Add a CSV import rule. Transactions matching keyword are auto-posted to account_name."""
    _init(db_path)
    # Verify the target account exists
    acct = models.get_account_by_name(account_name)
    if not acct:
        raise ValueError(f"Account not found: {account_name}")
    models.save_import_rule(None, keyword, account_name, tax_code, priority)
    # Retrieve the newly created rule to get its ID
    rules = models.get_import_rules()
    rule_id = None
    for r in rules:
        if r["keyword"] == keyword and r["account_name"] == account_name:
            rule_id = r["id"]
            break
    return {"rule_id": rule_id}


@mcp.tool()
def delete_rule(db_path: str, rule_id: int) -> dict:
    """Delete an import rule by ID."""
    _init(db_path)
    models.delete_import_rule(rule_id)
    return {"deleted": True, "rule_id": rule_id}


if __name__ == "__main__":
    mcp.run()

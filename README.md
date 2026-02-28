# GridTRX

**Command-line-first, agent-ready double-entry accounting framework.**

GridTRX is a double-entry bookkeeping system designed to be operated by AI agents, scripts, and power users from the terminal. Every operation — posting transactions, running reports, importing bank data, closing a fiscal year — works through a deterministic CLI with plain-text output. No mouse required.

A browser UI is included for visual work (ledger browsing, report layout, reconciliation), but the CLI is the primary interface.

## Why GridTRX

- **Agent-native.** One-shot CLI mode: `python cli.py /path/to/books.db tb` — runs a command, prints output, exits. AI agents can drive the entire accounting cycle without a browser.
- **Zero dependencies for CLI.** Python 3.7+ standard library only. No pip install, no venv, no Docker. Just `python cli.py`.
- **Single-file database.** Each set of books is one SQLite file (`books.db`). Copy it, back it up, email it. No server, no cloud, no accounts.
- **Real double-entry.** Every transaction balances. Debits equal credits. Trial balance always ties. No shortcuts, no single-entry hacks.
- **Opinionated defaults.** `new` creates a full chart of accounts (~60 posting, ~25 total), five reports (BS, IS, AJE, TRX, RE.OFS), 60+ import rules for common vendors, and four tax codes. You're posting transactions in seconds.

## Quick Start

```bash
# Create new books
python cli.py
Grid> new ~/clients/acme "Acme Corp"

# Post a transaction
Grid/Acme Corp> post 2025-01-15 "Office supplies" 84.00 EX.OFFICE BANK.CHQ

# Check the trial balance
Grid/Acme Corp> tb

# Run the balance sheet
Grid/Acme Corp> report BS

# Import a bank CSV
Grid/Acme Corp> importcsv ~/downloads/jan2025.csv BANK.CHQ
```

## AI Agent Usage

One-shot mode runs a single command and exits. Output is plain text to stdout.

```bash
# Trial balance
python cli.py ~/clients/acme tb

# Post a transaction
python cli.py ~/clients/acme post 2025-03-01 "Rent" 1500.00 EX.RENT BANK.CHQ

# Account balance
python cli.py ~/clients/acme balance BANK.CHQ

# Ledger with date range
python cli.py ~/clients/acme ledger BANK.CHQ 2025-01-01 2025-03-31

# Income statement for a period
python cli.py ~/clients/acme report IS 2025-01-01 2025-12-31

# Export trial balance to CSV
python cli.py ~/clients/acme exporttb tb.csv 2025-12-31

# Chain commands
python cli.py ~/clients/acme tb && \
python cli.py ~/clients/acme report BS && \
python cli.py ~/clients/acme report IS
```

**Output conventions:**
- Positive numbers = debits, negative (in parentheses) = credits, `—` = zero
- Success: lines start with `✓`
- Errors: lines start with `Error:` or `Cannot`
- Tables: header row, `───` separator, fixed-width columns

## Display Format

GridTRX uses raw accounting format everywhere in the CLI:

```
 1,500.00      ← $1,500 debit
(1,500.00)     ← $1,500 credit
    —          ← zero
```

Unambiguous. No sign-flipping. What you see is what's stored. Agents can parse it reliably.

## Commands

| Command | Description |
|---------|-------------|
| `new <folder> ["Name"] [MM-DD]` | Create new books with full chart of accounts |
| `open <path>` | Open existing books |
| `post <date> <desc> <amt> <dr> <cr>` | Post a 2-line transaction |
| `postx <date> <desc>` | Post a multi-line (compound) transaction |
| `tb [date]` | Trial balance |
| `report <name> [from] [to]` | Run a report (BS, IS, etc.) |
| `ledger <acct> [from] [to]` | Account ledger with running balance |
| `balance <acct> [from] [to]` | Single account balance |
| `importcsv <file> <acct>` | Import bank CSV with auto-categorization |
| `accounts [posting\|total]` | List chart of accounts |
| `find <query>` | Search accounts by name/description |
| `search <query>` | Search transactions by description/reference |
| `rules` | List import rules |
| `addrule <kw> <acct> [tax] [pri]` | Add an import rule |
| `ye <date>` | Year-end rollover |
| `lock [date]` | Show or set lock date |
| `exportcsv <report> [file]` | Export report to CSV |
| `exporttb [file] [date]` | Export trial balance to CSV |
| `reconcile <acct>` | Reconciliation summary |
| `taxcodes` | List tax codes |

Full CLI reference: [CLI_README.txt](CLI_README.txt)

## Browser UI

For visual work, start the web interface:

```bash
# Requires Flask (auto-installed on first run)
python run.py
```

Opens at `http://localhost:5000`. Same database, same data. Features include:

- Account ledgers with inline editing
- Report viewer with drill-down
- Multi-column comparative reports (up to 13 columns)
- Bank CSV import with rule matching preview
- Print-ready report output
- Reconciliation marking
- Dark mode

## Architecture

```
books.db          ← SQLite database (one per client)
models.py         ← Data layer — all reads/writes go through here
cli.py            ← Command-line interface (no dependencies)
app.py            ← Flask web UI (optional)
templates/        ← Jinja2 templates for browser UI
```

- **models.py** is the single source of truth. Both CLI and web UI call the same functions.
- Amounts are stored as integers (cents). No floating-point rounding issues.
- Transactions are always balanced (sum of all lines = 0).
- Reports use a total-to chain: posting accounts roll up through up to 6 levels of totals.

## Requirements

**CLI only:** Python 3.7+ (standard library only — no pip install needed)

**Browser UI:** Python 3.7+ and Flask (`pip install flask`, or just run `run.py` and it installs automatically)

## License

AGPLv3 — see [LICENSE](LICENSE)

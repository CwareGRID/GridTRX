Grid CLI — User Manual
======================

Grid CLI is the command-line interface for Grid, an open-source double-entry
bookkeeping system. It reads and writes the same SQLite database (books.db)
as the browser UI, but runs entirely in your terminal. No web server needed.
Type a command, get text back. That's it.


1. GETTING STARTED
==================

Grid CLI has three modes:

  Interactive (no file):
    python cli.py

    Starts a Grid> prompt. Use 'open <path>' to load a client's books,
    or 'new <folder>' to create new ones.

  Interactive (with file):
    python cli.py /path/to/books.db

    Opens the specified books and drops you into the REPL.

  One-shot:
    python cli.py /path/to/books.db tb

    Runs a single command and exits. This is what AI agents use.
    You can point to a folder instead of a file — Grid looks for books.db
    inside it automatically.

Requirements: Python 3.7+, no external packages. Grid uses only the
standard library (cmd, sqlite3, csv, json, os, sys, shlex, datetime).


2. CREATING YOUR FIRST BOOKS
=============================

Step 1 — Create the books:

    Grid> new ~/clients/acme "Acme Corp"

    This creates the folder ~/clients/acme/, initializes books.db with a
    full chart of accounts (~60 posting accounts, ~25 total accounts),
    five reports (BS, IS, AJE, TRX, RE.OFS), 60+ import rules for common
    Canadian vendors, and four tax codes (G5, H13, H15, E).

    The books are automatically opened after creation.

    You can specify a fiscal year-end if it's not December 31:

    Grid> new ~/clients/acme "Acme Corp" 03-31

Step 2 — Check the chart of accounts:

    Grid/Acme Corp> accounts

    This lists every account. To see only posting accounts (the ones
    you can post transactions to):

    Grid/Acme Corp> accounts posting

Step 3 — Post a transaction:

    Grid/Acme Corp> post 2025-01-15 "Office supplies" 84.00 EX.OFFICE BANK.CHQ

    This debits EX.OFFICE (Office & General) for $84.00 and credits
    BANK.CHQ (Bank - Chequing) for $84.00. A two-line journal entry.

Step 4 — Check the trial balance:

    Grid/Acme Corp> tb

    This shows all accounts with non-zero balances. Debits on the left,
    credits on the right. The totals should match.

Step 5 — Run a report:

    Grid/Acme Corp> report BS
    Grid/Acme Corp> report IS


3. IMPORTING BANK DATA
========================

Grid can import bank transaction CSVs and automatically categorize them
using import rules.

Prepare your CSV:

    Grid accepts three CSV formats:

      Simple (3-column):
        Date, Description, Amount

      Simple (4-column):
        Date, Description, Debit, Credit

      Multi-column bank export (5+ columns):
        Grid auto-detects date, description, and amount columns from the
        header. Headers containing "date" → date column, "description",
        "desc", "memo" → description, "$", "amount" → amount. Everything
        else (account type, account number, cheque number) is ignored.

        Example: a bank CSV with columns
          Account Type, Account Number, Transaction Date, Cheque Number,
          Description 1, Description 2, CAD$, USD$
        works directly — no conversion needed.

    The first row can be a header (Grid auto-detects it).
    Amounts: positive = deposits, negative = payments.

    Messy data: If a CSV row has more fields than the header (from
    unquoted commas in descriptions like "$10,000" or "Smith, John"),
    Grid automatically repairs it by merging the extra fields back into
    the description. The repair is reported in the import summary.

Import:

    Grid/Acme Corp> importcsv ~/downloads/jan2025.csv BANK.CHQ

    Grid reads each row, matches the description against import rules
    (highest priority first), and posts a transaction. If no rule matches,
    the transaction goes to EX.SUSP (Suspense).

How rules work:

    A rule maps a keyword to an account. When a bank description contains
    that keyword, the transaction is posted to that account.

    Grid/Acme Corp> rules

    This lists all rules. Each rule has:
      ID       — unique number (for editing/deleting)
      Keyword  — text to match (case-insensitive)
      Account  — where to post the transaction
      Tax      — tax code to apply (splits into net + tax amounts)
      Priority — higher number = matched first (breaks ties)

    Grid/Acme Corp> addrule SHOPIFY REV.SVC G5 10

    This creates a rule: when a bank description contains "SHOPIFY",
    post it to REV.SVC (Revenue - Services) with GST 5% tax split,
    priority 10.

    Grid/Acme Corp> editrule 42 SHOPIFY REV G5 15

    This edits rule #42 to change the account to REV and priority to 15.

    Grid/Acme Corp> delrule 42

    This deletes rule #42.

Handling suspense items:

    After importing, Grid tells you how many items went to suspense:

      3 items went to suspense (no matching rule).
      Review them: ledger EX.SUSP
      Add rules to prevent this: addrule <keyword> <account>

    View suspense: ledger EX.SUSP
    Each entry shows the bank description. Use that to create rules,
    then delete the suspense transactions and re-import.


4. UNDERSTANDING THE DISPLAY
==============================

Grid CLI uses raw accounting display everywhere:

    Positive numbers = Debits
    Negative numbers (in parentheses) = Credits
    Zero = — (em dash)

Examples:
    1,500.00     This is a $1,500 debit
    (1,500.00)   This is a $1,500 credit
    —            This is zero

This is different from the browser UI, which flips signs based on the
account's normal balance (so revenue shows as positive even though it's
a credit). The CLI never does this. What you see is what's in the database.

Why? Because it's unambiguous. You always know which side of the ledger
a number is on. AI agents rely on this predictability.


5. COMMANDS — REFERENCE
=========================

All commands are case-insensitive. Arguments in [brackets] are optional.


--- NAVIGATION ---

  open <path>
    Open a books.db file. You can pass a folder path and Grid will
    look for books.db inside it.
    Example: open ~/clients/acme

  close
    Close the current books. Returns to the Grid> prompt.

  info
    Show company name, fiscal year-end, lock date, database stats.

  library [path]
    List client folders in a library directory. If no path given,
    uses the library_path from grid.json.


--- SETUP ---

  new <folder> ["Company Name"] [MM-DD]
    Create new client books. Creates the folder if needed, initializes
    books.db with the full default chart of accounts, reports, rules,
    and tax codes. Auto-opens the new books after creation.

    If no company name given, derives one from the folder name.
    Fiscal year-end defaults to 12-31 if not specified.

    Examples:
      new ~/clients/acme
      new ~/clients/acme "Acme Corp"
      new ~/clients/acme "Acme Corp" 03-31

  addaccount <name> <D|C> <description> [posting|total]
    Add a new account to the chart of accounts.

    D = debit-normal (assets, expenses)
    C = credit-normal (liabilities, equity, revenue)
    Defaults to 'posting' type.

    Examples:
      addaccount EX.PARKING D "Parking Expense"
      addaccount TOTPARK D "Total Parking" total

    Note: new accounts are not automatically added to any report.
    Use the browser UI to place them on BS or IS.

  editaccount <name> [--desc "text"] [--num "1000"]
    Edit an account's description or account number.

    Examples:
      editaccount EX.RENT --desc "Office Rent"
      editaccount BANK.CHQ --num "1000"
      editaccount EX.RENT --desc "Office Rent" --num "5200"


--- ACCOUNTS ---

  accounts [posting|total]
    List all accounts. Optionally filter by type.
    'posting' = accounts you can post transactions to.
    'total'   = accounts that accumulate from other accounts via reports.

  account <name>
    Show details for one account: name, description, type, normal
    balance, account number, current balance, and which report it's on.

  find <query>
    Search accounts by name or description.
    Example: find bank


--- LEDGER ---

  ledger <account> [from_date] [to_date]
    Show all transactions for an account, with running balance.
    Amounts are raw: positive = debit, negative (parens) = credit.

    Examples:
      ledger BANK.CHQ
      ledger BANK.CHQ 2025-01-01 2025-03-31


--- TRANSACTIONS ---

  post <date> <desc> <amount> <debit_acct> <credit_acct>
    Post a simple 2-line transaction. The amount is always positive —
    the first account gets the debit, the second gets the credit.

    Example:
      post 2025-03-01 "March rent" 1500.00 EX.RENT BANK.CHQ

    This creates:
      Dr EX.RENT      1,500.00
      Cr BANK.CHQ    (1,500.00)

  postx <date> <desc>
    Post a multi-line transaction interactively. After entering the
    date and description, you enter lines one at a time:

      <account> <amount>

    Positive amounts = debit. Negative amounts = credit.
    Type 'done' when finished. The transaction must balance (debits
    must equal credits). Type 'cancel' to abort.

    Example:
      Grid/Acme Corp> postx 2025-03-15 "Office supplies"
      [0.00 off] line> EX.SAL 5000
      [5000.00 off] line> GST.IN 250
      [5250.00 off] line> BANK.CHQ -5250
      [0.00 off] line> done

  importcsv <csvfile> <bank_account>
    Import a bank CSV file. See section 3 for details.

  edit <txn_id>
    Show the full details of a transaction: date, reference,
    description, and all lines with amounts.

  delete <txn_id>
    Delete a transaction. Asks for confirmation. Cannot delete
    transactions on or before the lock date.

  search <query>
    Search transactions by description or reference.
    Example: search rent


--- REPORTS ---

  tb [as-of-date]
    Show the trial balance. All posting accounts with non-zero
    balances, split into Debit and Credit columns. Totals at bottom.

    Example:
      tb
      tb 2025-12-31

  report <name> [from_date] [to_date]
    Run a named report. Shows the report's structure with balances.

    Examples:
      report BS
      report IS 2025-01-01 2025-12-31

  reports
    List all defined reports (BS, IS, AJE, TRX, RE.OFS, etc.).

  balance <account> [from_date] [to_date]
    Show a single account's raw balance.

    Example: balance BANK.CHQ


--- EXPORT ---

  exportcsv <report> [filename] [from_date] [to_date]
    Export a report to a CSV file. Columns: Description, Account,
    Type, Balance. If no filename given, defaults to <report>.csv

    Examples:
      exportcsv BS
      exportcsv IS income_2025.csv 2025-01-01 2025-12-31

  exporttb [filename] [as-of-date]
    Export the trial balance to a CSV file. Columns: Account Number,
    Name, Description, Normal Balance, Debit, Credit, Raw Balance.
    Defaults to trial_balance.csv.

    Examples:
      exporttb
      exporttb trial_balance.csv 2025-12-31


--- RULES ---

  rules
    List all import rules with their IDs.

  addrule <keyword> <account> [tax_code] [priority]
    Add a new import rule.
    Example: addrule NETFLIX EX.COMP G5 10

  editrule <id> <keyword> <account> [tax_code] [priority]
    Edit an existing rule by ID. You must provide all fields.
    Example: editrule 5 NETFLIX EX.COMP G5 20

  delrule <id>
    Delete an import rule by ID. Asks for confirmation.
    Example: delrule 5


--- YEAR-END ---

  ye [YYYY-MM-DD]
    Year-end rollover. See section 7 for details.


--- OTHER ---

  reconcile <account>
    Show reconciliation summary: book balance, cleared balance,
    and uncleared balance. All in raw format.

  taxcodes
    List tax codes (e.g. G5 = GST 5%, H13 = HST 13%).

  lock [YYYY-MM-DD]
    Show or set the lock date. Transactions on or before the lock
    date cannot be posted, edited, or deleted.

  help
    Show the command summary.

  quit / exit
    Exit Grid CLI.


6. YEAR-END ROLLOVER
=====================

What it does:

    At the end of a fiscal year, the Income Statement accounts
    (revenue, expenses) need to be "closed" — their net result
    (profit or loss) gets carried forward to Retained Earnings.

    Grid handles this with a single journal entry:
      Dr RE.OFS    (the offset account)
      Cr RE.OPEN   (retained earnings opening balance)

    This entry is dated the first day of the NEW fiscal year.

When to run it:

    After you've posted all transactions for the fiscal year and
    are ready to start the next year. Typically after filing taxes.

What happens:

    1. Grid computes RE.CLOSE from the IS report as of the YE date.
       RE.CLOSE is the bottom line — net income after all revenue
       and expenses roll up through the total-to chain.

    2. Grid posts a journal entry on the first day of the new year
       that moves this amount into RE.OPEN via RE.OFS.

    3. Grid sets the lock date to the fiscal year-end date, preventing
       any changes to transactions in the closed year.

    4. Grid updates the fiscal year metadata.

How to run it:

    Grid/Acme Corp> ye 2025-12-31

    Grid shows you the entry before posting and asks for confirmation.

Important: Year-end rollover is a one-way operation. The lock date
prevents changes to the closed year. If you need to make corrections,
you'll need to change the lock date first (lock <date>).

No reset: Grid uses perpetual totals. There is no "year-end close"
that zeros out accounts. The IS report naturally filters by date range.
The YE entry just carries the net result forward in RE.


7. TROUBLESHOOTING
====================

"Account not found"
    The account name doesn't match anything in the chart of accounts.
    Try: accounts (to list all) or find <query> (to search).
    Account names are case-insensitive. Partial names work if
    there's only one match (e.g. "bank" matches "BANK.CHQ" if
    it's the only account with "bank" in the name).

"Ambiguous account"
    Your search matches multiple accounts. Use the full name.
    Grid shows you the matches so you can pick the right one.

"Cannot post — books are locked through YYYY-MM-DD"
    The transaction date is on or before the lock date.
    The lock date protects closed periods from changes.
    Check the lock date: lock
    Change it if needed: lock <new-date>

"Cannot post to 'TOTAL' — it is a total account"
    You can only post transactions to 'posting' accounts.
    Total accounts accumulate from posting accounts via reports.
    See posting accounts: accounts posting

"Invalid date"
    Use YYYY-MM-DD format (e.g. 2025-03-15).
    Grid also accepts M/D/YYYY and D/M/YYYY formats.

"Invalid amount"
    Valid formats: 1500, 1500.00, 1,500.00, (500), -500, $1,500.00

"Transaction does not balance"
    In postx, debits must equal credits. Grid shows you the
    imbalance and tells you how much more you need on each side.

"OUT OF BALANCE"
    The trial balance doesn't balance. This shouldn't happen in
    normal use — every transaction is double-entry. Check for
    accounts that aren't on any report (account <name>).

"No books open"
    You need to open a database first.
    Use: open <path>  or  new <folder>

"File not found"
    Check the file path. You can use ~ for home directory.
    If the books don't exist yet, create them: new <folder>


8. FOR AI AGENTS
=================

One-shot mode:

    python cli.py /path/to/books.db <command>

    Runs a single command and exits. Output goes to stdout.
    Errors go to stdout too (not stderr). Exit code is always 0
    unless the database file doesn't exist (exit code 1).

Examples:

    python cli.py ~/clients/acme tb
    python cli.py ~/clients/acme balance BANK.CHQ
    python cli.py ~/clients/acme post 2025-03-01 "Rent" 1500.00 EX.RENT BANK.CHQ
    python cli.py ~/clients/acme search rent
    python cli.py ~/clients/acme accounts posting
    python cli.py ~/clients/acme ledger BANK.CHQ 2025-01-01 2025-03-31
    python cli.py ~/clients/acme report IS 2025-01-01 2025-12-31
    python cli.py ~/clients/acme exporttb tb.csv 2025-12-31

Chaining commands:

    Use shell && to chain commands:

    python cli.py ~/clients/acme tb && \
    python cli.py ~/clients/acme report BS && \
    python cli.py ~/clients/acme report IS

Output format:

    All output is plain text, indented with two spaces. Tables use
    fixed-width columns aligned with spaces. Numbers use raw
    accounting format: positive = debit, negative in parens = credit.

    Amount parsing accepts: 1500, 1500.00, 1,500.00, (500), -500

Creating new books from a script:

    python cli.py  (then pipe commands via stdin)
    Or use one-shot mode with 'new' — note that 'new' doesn't
    require an existing database path:

    python cli.py                          # starts interactive
    # Then: new ~/clients/acme "Acme Corp"

    For scripted creation, start interactive mode and pipe:
    echo 'new ~/clients/acme "Acme Corp"' | python cli.py

Expected response patterns:

    Success lines start with "  ✓"
    Error lines start with "  Error:" or "  Cannot"
    Data tables have a header row followed by a ─── separator
    Empty results say "  (no data)" or "  (no entries)"

    Parse the ✓ character to confirm operations succeeded.

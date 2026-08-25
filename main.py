from contextlib import contextmanager, nullcontext
from datetime import datetime
from itertools import batched
from pypdf import PdfReader

import argparse
import csv
import sys

PDF_HEADER_STR = "Date Transaction details Amount Balance"

DATE_FMT = "%d %b %Y"
TRANSACTION_LINES = 3  # title \n note \n amounts
CSV_HEADER_FIELDS = ["date", "note", "amount", "desc"]

parser = argparse.ArgumentParser(
    prog="chase-to-csv",
    description="Convert Chase UK PDF statement to hledger-importable CSV",
)
parser.add_argument("-f", "--files", nargs="+", required=True)
parser.add_argument("-o", "--out")
parser.add_argument("--use-old-parsing", action="store_true")

args = parser.parse_args()

transactions = []
for f in args.files:
    reader = PdfReader(f)
    pages = reader.pages

    start = None
    done = False
    failed = False
    for page_no, page in enumerate(pages):
        if done or failed:
            break

        lines = page.extract_text().splitlines()
        start = lines.index(PDF_HEADER_STR)
        if start == -1:
            print(f"Didn't find header string on page {page_no + 1}", file=sys.stderr)
            continue

        # TODO: figure out when they changed this/auto-detect it
        #       it used to be that the opening -> closing bal
        #       was at the end of the page
        if args.use_old_parsing:
            lines[:] = lines[
                : next(
                    (
                        i
                        for i in range(len(lines) - 1, -1, -1)
                        if "Account statement" in lines[i]
                    ),
                    len(lines),
                )
            ]

        skip = 2 if page_no == 0 else 1

        for group in batched(lines[start + skip :], TRANSACTION_LINES):
            if group[0].startswith("Page"):
                continue
            if "Closing balance" in group[0]:
                done = True
                break

            try:
                datestr = group[0][:11]
                date = datetime.strptime(datestr, DATE_FMT)
            except ValueError:
                print(f"failed to parse date from {datestr}")
                done = True
                failed = True
                break

            desc = group[0][12:]
            note = group[1]
            amount = group[2].split(" ")[0].replace("£", "")

            transactions.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "desc": desc,
                    "note": note,
                    "amount": amount,
                }
            )

if start is None or start == -1:
    print("Didn't find a line matching '" + PDF_HEADER_STR + "'", file=sys.stderr)
    exit()

if failed:
    exit(1)


@contextmanager
def output_stream(path):
    if path:
        with open(path, "a", newline="") as stream:
            yield stream
    else:
        yield sys.stdout


with output_stream(args.out) as stream:
    writer = csv.DictWriter(stream, fieldnames=CSV_HEADER_FIELDS)
    writer.writeheader()
    writer.writerows(transactions)

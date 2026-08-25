from datetime import datetime
from itertools import batched
from pypdf import PdfReader

import argparse
import csv

PDF_HEADER_STR = "Date Transaction details Amount Balance"

DATE_FMT = "%d %b %Y"
TRANSACTION_LINES = 3 # title \n note \n amounts
CSV_HEADER_FIELDS = ["date","note","amount","desc"]

parser = argparse.ArgumentParser(
                    prog='chase-to-csv',
                    description='Convert Chase UK PDF statement to hledger-importable CSV')
parser.add_argument("target_pdf")

args = parser.parse_args()
reader = PdfReader(args.target_pdf)
pages = reader.pages

transactions = []
start = None
done = False
failed = False
for page_no, page in enumerate(pages):
    if done or failed: break

    lines = page.extract_text().splitlines()
    start = lines.index(PDF_HEADER_STR)
    if start == -1:
        print(f"Didn't find header string on page {page_no+1}", file=sys.stderr)
        continue

    skip = 2 if page_no == 0 else 1

    for group in batched(lines[start+skip:], TRANSACTION_LINES):
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
        amount= group[2].split(" ")[0].replace("£", "")

        transactions.append({ "date": date.strftime("%Y-%m-%d"), "desc": desc, "note": note, "amount": amount })

if start is None or start == -1:
    print("Didn't find a line matching '" + PDF_HEADER_STR + "'", file=sys.stderr)
    exit()

if failed:
    exit(1)

with open('transactions.csv', 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADER_FIELDS)
    writer.writeheader()
    for t in transactions: writer.writerow(t)

#!/usr/bin/env python3
"""
renumber_clauses.py   ·   TPTP ax_claused label normaliser

Usage:
    python renumber_clauses.py  input.ax_claused.txt  [output.txt]

If no output file is given the script writes
<basename>.renum.ax_claused.txt next to the input file.
"""
import re, itertools, pathlib

FILE_NAME = "generated_axioms.ax_claused.txt"

LABEL_PREFIX = "u"                                   # keep or change as needed
PATTERN = re.compile(rf'\b(cnf|fof)\(\s*{LABEL_PREFIX}\d+\s*,', re.IGNORECASE)
COUNTER = itertools.count(1)

file_path = pathlib.Path(__file__).with_name(FILE_NAME)

# Read, transform, and write back to the same file
new_lines = []
with file_path.open(encoding="utf‑8") as fin:
    for line in fin:
        # Replace at most one label per line (the clause header)
        new_line = PATTERN.sub(
            lambda m: f"{m.group(1)}({LABEL_PREFIX}{next(COUNTER)},",
            line,
            count=1,
        )
        new_lines.append(new_line)

file_path.write_text("".join(new_lines), encoding="utf‑8")
print(f"✔ Renumbered clauses saved back to {file_path}")

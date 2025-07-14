import glob, json, re, collections, sys, os, pathlib

folder = sys.argv[1] if len(sys.argv) > 1 else "Res_Pairs"
pattern = os.path.join(folder, "*.jsonl")

preds = collections.OrderedDict()     # preserves order of first appearance

for fn in glob.glob(pattern):
    with open(fn, "r", encoding="utf-8") as f:
        obj = json.load(f)            # each file is a single JSON object
        for _cid, _ctype, literals in obj["clauses"]:
            for lit in literals:
                m = re.match(r'\s*[~¬]?\s*([A-Za-z0-9_]+)\(', lit)
                if m:
                    preds.setdefault(m.group(1), None)

print(" ".join(preds))                # space-separated list for the CLI

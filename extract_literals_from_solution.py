import os, glob, re, json

# -----------------------------------------------------------------------------
#  extract_solution_v2.py  —  updated version of the user’s original script
# -----------------------------------------------------------------------------
#  Changes in this file (all original comments kept):
#   * new helper `vamp_id_to_index()`
#   * per‑clause loop inside `process_files()` rewritten to
#       – try fast numeric index lookup first, then
#       – fall back to slow text matching only if necessary.
#   * nothing else removed; the heavyweight helpers remain for robustness /
#     debugging.
# -----------------------------------------------------------------------------


def vamp_id_to_index(cid: str) -> int:
    """Return 0‑based guess for the position of an original clause.

    Vampire numbers all input clauses (both fof/ and their clausified cnf/u‑variants)
    with a *1‑based* integer suffix:
        f1, f2, … / u1, u2, …
    In most generated problems that integer equals the array index + 1 in the
    JSONL file.  So   f19  →  18.
    This is only a *hint*; we still verify the clause text later.
    """
    return int(re.search(r"\d+", cid)[0]) - 1


# -----------------------------------------------------------------------------
#  Helpers copied verbatim from the original script
# -----------------------------------------------------------------------------

def find_first_original_inference_by_role(solved_text):
    """
    Scan all inference(...) annotations bottom‑up and return the first one
    where BOTH clause‑IDs refer to a fof(..., axiom, ...) or
    fof(..., negated_conjecture, ...).
    """
    # 1) find every inference(...) line
    inf_pattern = (
        r"fof\(f\d+,\w+,\(\s*(.*?)\s*\)\s*,\s*inference\(([^,]+),\s*\[[^\]]*\],\s*\[([^\]]+)\]\)\)"
    )
    matches = list(re.finditer(inf_pattern, solved_text, re.DOTALL))

    # 2) helper to look up a clause's “role” (axiom / negated_conjecture / ...)
    def get_role(clause_id):
        m = re.search(rf"fof\({re.escape(clause_id)},\s*([^,]+)\s*,", solved_text)
        return m.group(1).strip() if m else None

    # 3) scan from the bottom (last in the file) upward
    for m in reversed(matches):
        formula = m.group(1).strip()
        inf_type = m.group(2).strip()
        clause_ids = [cid.strip() for cid in m.group(3).split(',')]
        roles = [get_role(cid) for cid in clause_ids]

        # accept only if both roles are in our original set
        if all(r in ("axiom", "negated_conjecture") for r in roles):
            return formula, inf_type, clause_ids

    # 4) fallback to the very last inference if none matched
    if matches:
        last = matches[-1]
        formula = last.group(1).strip()
        inf_type = last.group(2).strip()
        clause_ids = [cid.strip() for cid in last.group(3).split(',')]
        return formula, inf_type, clause_ids

    return None, None, []


def extract_clause_text(solved_text, clause_id):
    """
    Find the full clause text (with nested parens) for fof(clause_id, ...)
    Returns: (clause_role, clause_body)
    """
    header = f"fof({clause_id},"
    idx = solved_text.find(header)
    if idx == -1:
        return None, None

    # move to just past the clause_id comma
    idx += len(header)
    # find the comma after the role name
    comma_after_role = solved_text.find(',', idx)
    role = solved_text[idx:comma_after_role].strip()

    # now find the '(' that opens the clause‑term
    open_paren = solved_text.find('(', comma_after_role + 1)
    if open_paren == -1:
        return role, None

    # walk forward to find matching closing paren
    depth = 0
    for j in range(open_paren, len(solved_text)):
        if solved_text[j] == '(':  # opening paren
            depth += 1
        elif solved_text[j] == ')':
            depth -= 1
            if depth == 0:
                close_paren = j
                break
    else:
        return role, None

    # extract everything inside those outer parens
    clause_body = solved_text[open_paren + 1: close_paren].strip()
    return role, clause_body


def normalize_clause(clause_text) -> set[str]:
    """
    Return a set of predicate fingerprints like  'pred' or '~pred'
    (sign + predicate name, arguments discarded).  Robust against
    extra parentheses, empty literals, infix '=', and TPTP built‑ins.
    """
    txt = clause_text.strip()

    # ── Remove outer (quantifiers …) and all whitespace ───────────────────────
    quant_pat = r"^\(\s*!\s*\[[^\]]*\]\s*:\s*\(\s*(.*)\s*\)\s*\)\s*$"
    m = re.match(quant_pat, txt, re.DOTALL)
    body = m.group(1) if m else txt
    body = re.sub(r"\s+", "", body)        # drop all blanks

    # ── Split on disjunction ─────────────────────────────────────────────────
    raw_lits = [lit for lit in body.split('|') if lit]   # ignore empty pieces
    fingerprints = []

    for lit in raw_lits:
        lit = lit.strip('()')               # remove outer parentheses
        sign = '~' if lit.startswith('~') else ''
        core = lit[1:] if sign else lit     # drop the '~' for the regex

        # equality in infix form  X=Y  → pretend predicate 'eq'
        if '=' in core and not core.startswith('$'):
            pred = 'eq'
        else:
            m_pred = re.match(r'([A-Za-z_$][A-Za-z0-9_$]*)', core)
            if not m_pred:
                # Something exotic (numbers only, empty, etc.) – skip it
                continue
            pred = m_pred.group(1).lstrip('$')  # for $less → less

        fingerprints.append(sign + pred)

    return set(fingerprints)
    # """
    # Strip outer quantifiers/parens and return a *set* of literals.
    # Example             →  ~p(X)|q(Y)
    # (order & whitespace are irrelevant for equality testing)
    # """
    # txt = clause_text.strip()

    # # strip universal quantifier if present
    # m = re.match(r"^\(\s*!\s*\[[^\]]+\]\s*:\s*\(\s*(.*)\s*\)\s*\)\s*$", txt, re.DOTALL)
    # if m:
    #     body = m.group(1)
    # else:
    #     body = txt[1:-1] if txt.startswith('(') and txt.endswith(')') else txt

    # body = re.sub(r"\s+", "", body)  # drop all whitespace
    # return set(body.split('|'))


# def find_matching_cnf_clause(problem_clauses, formula_text):
#     """Slow O(n) scan that returns the first clause with identical literal set."""
#     norm = normalize_clause(formula_text)

#     # exact match
#     for c in problem_clauses:
#         if normalize_clause(c["text"]) == norm:
#             return c
#     return None

def get_literal_name(literal):
    """Extract the predicate name from a literal, ignoring variables and negation."""
    # Remove negation if present
    if literal.startswith('~'):
        literal = literal[1:]
    # Extract the predicate name (before first '(')
    return literal.split('(', 1)[0]

def find_resolved_literals(parent1_text, parent2_text, resolvent_text):
    """
    Identify which literals were resolved by comparing parent clauses with resolvent.
    Returns: (literal_from_parent1, literal_from_parent2) that were resolved/unified,
             comparing only predicate names (ignoring variable renaming).
    """
    def process_clause(text):
        lits = normalize_clause(text)
        return {get_literal_name(lit): lit for lit in lits}
    
    # Get all literals indexed by their predicate names
    parent1_lits = process_clause(parent1_text)
    parent2_lits = process_clause(parent2_text)
    resolvent_lits = process_clause(resolvent_text)
    
    # Find predicate names missing in resolvent
    resolved_preds_p1 = set(parent1_lits.keys()) - set(resolvent_lits.keys())
    resolved_preds_p2 = set(parent2_lits.keys()) - set(resolvent_lits.keys())
    
    # We expect exactly one predicate from each parent to be resolved
    if len(resolved_preds_p1) != 1 or len(resolved_preds_p2) != 1:
        return None, None
    
    # Get the actual literals (with variables) that were resolved
    pred_p1 = resolved_preds_p1.pop()
    pred_p2 = resolved_preds_p2.pop()
    lit_p1 = parent1_lits[pred_p1]
    lit_p2 = parent2_lits[pred_p2]
    
    # Check if they're complementary (same predicate name with one negated)
    name_p1 = get_literal_name(lit_p1)
    name_p2 = get_literal_name(lit_p2)
    
    if name_p1 == name_p2 and ((lit_p1.startswith('~') ^ lit_p2.startswith('~'))):
        return lit_p1, lit_p2
    
    return None, None

def write_best_pair(json_path: str,
                    pair_dict: dict,
                    literal_pair: tuple | None):
    """
    • Load the single‑object JSONL → dict.
    • Ensure `resolvable_pairs` exists and contains `pair_dict`.
    • Write the index of that dict into `best_pair_index`.
      (flip the OPTION block below if you prefer storing the whole pair.)
    """
    with open(json_path, "r", encoding="utf‑8") as fp:
        data = json.load(fp)

    # OPTION A – store just the index
    if pair_dict:                      # ← found a real pair
        # make sure the list exists
        rp = data.setdefault("resolvable_pairs", [])

        # try to find existing identical entry
        try:
            idx = next(i for i, p in enumerate(rp) if p == pair_dict)
        except StopIteration:
            idx = len(rp)
            rp.append(pair_dict)

        # annotate resolved‑literals (optional, for human inspection)
        # pair_dict.setdefault("literal_pair", {
        #     "from_A": literal_pair[0] if literal_pair else None,
        #     "from_B": literal_pair[1] if literal_pair else None,
        # })
        data["best_pair_index"] = idx
    else:                              # ← nothing found
        data["best_pair_index"] = None
    #data["best_pair_index"] = idx

    # OPTION B – comment out the line above and uncomment below
    # data["best_pair"] = pair_dict

    with open(json_path, "w", encoding="utf‑8") as fp:
        json.dump(data, fp, ensure_ascii=False)
        fp.write("\n")          # keep the *JSONL* flavour (one object per line)


# ---------------------------------------------------------------------------
#  Main driver (problem JSONL ↔ proof log)
# ---------------------------------------------------------------------------

def process_files(problem_folder, output_folder):
    # only jsonl files ending with '_rs.jsonl'
    problem_files = glob.glob(os.path.join(problem_folder, "*_rs.jsonl"))
    if not problem_files:
        print(f"No problem files found in {problem_folder}")
        return

    for problem_file in problem_files:
        base = os.path.basename(problem_file)
        name_no_ext = os.path.splitext(base)[0]
        clean = name_no_ext[:-3] if name_no_ext.endswith("_rs") else name_no_ext

        solved_file = os.path.join(output_folder, clean + "_solved.txt")
        if not os.path.exists(solved_file):
            print(f"Solution file not found for {base}: {solved_file}")
            continue

        print(f"\n==== Processing: {base} ====")

        # --- load clauses (unchanged) ---
        with open(problem_file, 'r', encoding='utf-8') as f:
            data = json.loads(f.readline())
            raw_clauses = data.get("clauses", [])
            problem_clauses = [
                {"id": e[0], "type": e[1], "text": "|".join(e[2])}
                for e in raw_clauses
            ]

        # --- load Vampire proof (unchanged) ---
        with open(solved_file, 'r', encoding='utf-8') as f:
            proof = f.read()

        formula, inf_type, clause_ids = find_first_original_inference_by_role(proof)
        if not inf_type or len(clause_ids) != 2:
            print("  ↳ Skipping (need a binary inference on originals).")
            write_best_pair(problem_file, {}, None) 
            continue

        # ------------------------------------------------------------------
        #  Map both Vampire IDs → clause/literal indices
        # ------------------------------------------------------------------
        mapping = {}
        for cid in clause_ids:
            # 1) always extract the proof‑side clause text for verification
            _role, proof_txt = extract_clause_text(proof, cid)
            guessed_idx = vamp_id_to_index(cid)
            match_idx = (
                guessed_idx
                if 0 <= guessed_idx < len(problem_clauses)
                and normalize_clause(proof_txt)
                == normalize_clause(problem_clauses[guessed_idx]["text"])
                else None
            )
            if match_idx is None:
                # fallback slow scan
                for j, c in enumerate(problem_clauses):
                    if normalize_clause(proof_txt) == normalize_clause(c["text"]):
                        match_idx = j
                        break
            if match_idx is None:
                print(f"  ✗ Could not map clause {cid} to JSONL entry – skipped.")
                write_best_pair(problem_file, {}, None)
                break
            mapping[cid] = (match_idx, proof_txt)
        else:
            # both parents mapped → identify literal indices in each parent
            cid1, cid2 = clause_ids
            lit1, lit2 = find_resolved_literals(
                mapping[cid1][1], mapping[cid2][1], formula
            )

            if lit1 is None:
                print("  ⚠ Resolved literals not detected – file still updated w/o them.")

            # locate literal indices inside the stored clause‑texts
            def literal_index(clause_txt: str, literal: str) -> int | None:
                lits = list(normalize_clause(clause_txt))
                try:
                    return lits.index(re.sub(r"\s+", "", literal))
                except ValueError:
                    return None

            lit_idx1 = (literal_index(mapping[cid1][1], lit1)
                        if lit1 else None)
            lit_idx2 = (literal_index(mapping[cid2][1], lit2)
                        if lit2 else None)

            best_pair = {
                "clauseA_index": mapping[cid1][0],
                "literalA_index": lit_idx1,
                "clauseB_index": mapping[cid2][0],
                "literalB_index": lit_idx2,
            }

            print(f"  ✓ Best pair: {best_pair}")
            write_best_pair(problem_file, best_pair, (lit1, lit2))

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Configure these paths for your system
    problem_folder = "Res_Pairs"    # Folder containing the .jsonl files
    output_folder = "Output_Copy"        # Folder containing the _solved.txt files

    process_files(problem_folder, output_folder)

from typing import List, Dict, Any
import random

from unification_resolution import UnificationResolution

# def serializa_clauses(clauses) -> Dict[str, Any]:
#     """
#     Given a list of clauses (each tuple: (name, role, clause) where clause is a set of literals),
#     returns a dictionary with:
#       - "clauses": the input list,
#     """

#     # Create a JSON-serializable version of clauses
#     serializable_clauses = []
#     for nameA, roleA, clauseA in clauses:
#         # Convert set to list for JSON serialization
#         serializable_clauses.append([nameA, roleA, list(clauseA)])

#     return {
#         "clauses": serializable_clauses
#     }


MAX_PAIRS = 20               # <- keep at most this many candidate pairs

def find_candidate_resolvable_pairs(
    clauses: List[tuple]
) -> Dict[str, Any]:
    """
    Args:
      clauses – list of (name, role, clause_set)

    Returns a *single* JSON‑serialisable training example.
    """
    resolver = UnificationResolution()

    # ---- Serialise clauses -------------------------------------------------
    serializable_clauses = [
        [name, role, list(clause)] for name, role, clause in clauses
    ]

    # ---- Collect all resolvable literal pairs ------------------------------
    candidates: List[Dict[str, int]] = []
    for i, (_, _, clauseA) in enumerate(clauses):
        litsA = list(clauseA)
        for j in range(i + 1, len(clauses)):
            litsB = list(clauses[j][2])
            for a_idx, lA in enumerate(litsA):
                for b_idx, lB in enumerate(litsB):
                    if resolver.can_resolve(lA, lB) is not None:
                        candidates.append({
                            "clauseA_index": i,
                            "literalA_index": a_idx,
                            "clauseB_index": j,
                            "literalB_index": b_idx
                        })

    if not candidates:          # no resolvable pair at all
        return {
            "clauses": serializable_clauses,
            "resolvable_pairs": [],
            "best_pair_index": None          # unsat / trivial case
        }

    # “best” = first pair (you can change to any scoring you like)
    best_pair = candidates[0]

    # ---- Down‑sample while preserving the label ----------------------------
    if len(candidates) > MAX_PAIRS:
        # keep the label, sample the rest
        others = random.sample(candidates[1:], MAX_PAIRS - 1)
        candidates = [best_pair] + others

    # locate the label’s index *inside* the (possibly shuffled) list
    best_pair_index = candidates.index(best_pair)

    return {
        "clauses":           serializable_clauses,
        "resolvable_pairs":  candidates,
        "best_pair_index":   best_pair_index
    }


if __name__ == "__main__":
    import glob, os, json
    from create_examples_helpers import parse_tptp_clauses
    #or prob_path in glob.glob('Gen_Problems_Clausified/*.p'):
    for prob_path in glob.glob('Gen_Problems_Copy/*.p'):
        clauses = parse_tptp_clauses(prob_path)
        resolvable_pairs = find_candidate_resolvable_pairs(clauses)
        base = os.path.splitext(os.path.basename(prob_path))[0]
        json_filename = f'Res_Pairs/{base}_rs.jsonl'
        with open(json_filename, 'w') as fp:
            json.dump(resolvable_pairs, fp)
        print(f"Wrote {json_filename}")

# if __name__ == "__main__":
#     from create_examples import parse_tptp_clauses

#     fileName = "CAT001-0"
#     for k in range(10):
#         problem = parse_tptp_clauses(f'Gen_Problems/gen_problem_{k}_{fileName}.p')

#         resolvable_pairs = find_candidate_resolvable_pairs(problem)

#         print("Candidate Resolvable Pairs:")
#         for pair in resolvable_pairs["resolvable_pairs"]:
#             print(pair)

        
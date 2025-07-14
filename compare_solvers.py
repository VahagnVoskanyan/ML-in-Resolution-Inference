# benchmark_solver.py
#
# Compare two modes on a folder of *.jsonl problems
#   1. brute‑force resolution order  (your original solver)
#   2. GNN‑guided order              (same search, but pairs are tried
#      in descending score given by the checkpoint)

import os, glob, json, argparse, time
from collections import defaultdict
from typing import Dict, List, Tuple, Any

import torch
from train_model_GNN import (               # ← comes from your unchanged file
    EdgeClassifierGNN,
    build_graph_from_example,
    embed_literal, parse_literal,           # only needed if you tweak below
)
from problem_solver import (           # ← unchanged baseline prover
    load_clauses_from_jsonl,
    resolution_prover,
    UnificationResolution,                  # imported transitively
)

###############################################################################
# 1)  Helper: single‑step GNN score for every candidate pair
###############################################################################
def rank_pairs(example, model, p2i, device, max_args=3):
    """Return a list [(score, pair_dict), …] sorted high→low."""
    data = build_graph_from_example(example, p2i, max_args=max_args).to(device)
    with torch.no_grad():
        logits = model(data.x, data.edge_index)[:, 1]      # probability “best”
    # ignore the final “reversed” edge that build_graph_from_example appends
    scores = logits.cpu().tolist()[:-1]
    ranked = sorted(
        zip(scores, example["resolvable_pairs"]), key=lambda x: x[0], reverse=True
    )
    return ranked


###############################################################################
# 2)  Guided prover (identical to brute force, pair‑order differs)
###############################################################################
def resolution_prover_guided(clauses, model, p2i, device, max_args=3, max_clause_size=8, timeout_seconds=30) -> Tuple[bool, int]:
    """
    Guided resolution prover with:
      - GNN-ranked candidate ordering
      - max_clause_size limit
      - timeout mechanism
    Returns (proved: bool, steps: int).
    """

    ur = UnificationResolution()
    all_clauses = {frozenset(c) for c in clauses}
    new_clauses: set[frozenset] = set()
    processed_pairs: set[Tuple[Any, ...]] = set()
    step_count = 0
    start_time = time.time()

    while True:
        if time.time() - start_time > timeout_seconds:
            return False, step_count

        # Build “example” on‑the‑fly for the current clause set
        example = {
            "clauses": [["u", "tmp", list(c)] for c in all_clauses],
            "resolvable_pairs": [],
        }
        clause_list = sorted(all_clauses)
        for i, c1 in enumerate(clause_list):
            for j in range(i + 1, len(clause_list)):
                c2 = clause_list[j]
                for a, litA in enumerate(c1):
                    for b, litB in enumerate(c2):
                        example["resolvable_pairs"].append(
                            {
                                "clauseA_index": i,
                                "literalA_index": a,
                                "clauseB_index": j,
                                "literalB_index": b,
                            }
                        )

        # Rank candidate pairs with the GNN
        ranked = rank_pairs(example, model, p2i, device, max_args)
        
        for _score, pair in ranked:
            if time.time() - start_time > timeout_seconds:
                return False, step_count

            i, a = pair["clauseA_index"], pair["literalA_index"]
            j, b = pair["clauseB_index"], pair["literalB_index"]
            c1, c2 = clause_list[i], clause_list[j]

            key = (c1, c2, a, b)
            if key in processed_pairs:
                continue
            processed_pairs.add(key)

            litA, litB = list(c1)[a], list(c2)[b]
            subst = ur.can_resolve(litA, litB)
            if subst is None:
                continue

            # Construct resolvent -------------------------------------------
            resolvent = set()
            resolvent.update(
                ur.apply_subst_to_literal(l, subst) for l in c1 if l != litA
            )
            resolvent.update(
                ur.apply_subst_to_literal(l, subst) for l in c2 if l != litB
            )

            step_count += 1

            if not resolvent:               # ❑ derived – proof completed
                return True, step_count

            if len(resolvent) > max_clause_size:
                continue                    # drop overly long resolvents

            res_fs = frozenset(resolvent)
            if res_fs not in all_clauses and res_fs not in new_clauses:
                new_clauses.add(res_fs)

        if not new_clauses:
            return False, step_count         # saturation reached without ⊥

        all_clauses.update(new_clauses)
        new_clauses.clear()


###############################################################################
# 3)  CLI driver
###############################################################################
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problems", required=True,
                    help="Folder with *.jsonl problems")
    ap.add_argument("--checkpoint", default="Models/gnn_model1.pt")
    ap.add_argument("--predicates", nargs="+",
                    default=["pred1", "pred2", "pred3", "pred4", "pred5"])
    ap.add_argument("--max_args", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=10)
                    
    args = ap.parse_args()

    max_resolvent_size = 8 # 
    use_subsumption = False  # Enable subsumption in brute-force Prover

    # ── load model ────────────────────────────────────────────────────────────
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = EdgeClassifierGNN(num_predicates=len(args.predicates),
        max_args=args.max_args,
        hidden_dim=64).to(device)
    model.load_state_dict(torch.load(args.checkpoint, map_location=device))
    model.eval()

    p2i = {p: i + 1 for i, p in enumerate(args.predicates)}

    # ── run over all problems ─────────────────────────────────────────────────
    rows = []
    guided_better = 0
    #files = sorted(glob.glob(os.path.join(args.problems, "*.jsonl")))  #####
    for fn in sorted(glob.glob(os.path.join(args.problems, "*.jsonl"))):
        clauses = load_clauses_from_jsonl(fn)                      # baseline helper
        if not clauses:
            continue

        # - BRUTE‑FORCE -
        proved_bf, steps_bf, timed_out_bf = resolution_prover(clauses,
                            max_clause_size = max_resolvent_size,
                            timeout_seconds = args.timeout, 
                            use_subsumption = use_subsumption)    # from solver file

        # - GNN‑GUIDED -
        proved_gn, steps_gn = resolution_prover_guided(
            clauses, model, p2i, device, 
            args.max_args, max_resolvent_size, args.timeout 
        )

        rows.append((os.path.basename(fn), proved_bf, steps_bf, proved_gn, steps_gn))
        if steps_gn < steps_bf:
            guided_better += 1 

        # status for brute: treat timeout or failure as Not proved
        status_bf = "✓" if proved_bf else "✗"
        status_gn = "✓" if proved_gn else "✗"

        # print(f"{fn:40s}  brute: {steps_bf:4d} {status_bf:10s}   "
        #       f"guided: {steps_gn:4d} {status_gn}")
        
        print(f"{fn:40s}  brute: {steps_bf:4d} {status_bf}   guided: {steps_gn:4d} {status_gn}")

    # ── summary ───────────────────────────────────────────────────────────────
    # if rows:
    #     avg_bf = sum(r[2] for r in rows) / len(rows)
    #     avg_gn = sum(r[4] for r in rows) / len(rows)
    #     gain = (avg_bf - avg_gn) / avg_bf * 100 if avg_bf else 0
    #     pct_better = guided_better / len(rows) * 100

    #     print("\n──────────────── summary ────────────────")
    #     print(f"files tested: {len(rows)}")
    #     print(f"avg steps – brute‑force : {avg_bf:.1f}")
    #     print(f"avg steps – GNN‑guided  : {avg_gn:.1f}")
    #     print(f"relative reduction      : {gain:.1f} %")
    #     print(f"guided faster on        : {guided_better}/{len(rows)} "
    #           f"files  ({pct_better:.1f} %)")
        
    # ── summary ───────────────────────────────────────────────────────────────
    if rows:
        # Separate solved / unsolved for each mode
        solved_bf = [r[2] for r in rows if r[1]]       # steps where brute solved
        solved_gn = [r[4] for r in rows if r[3]]       # steps where guided solved

        unsolved_bf = len(rows) - len(solved_bf)
        unsolved_gn = len(rows) - len(solved_gn)

        avg_bf = sum(solved_bf) / len(solved_bf) if solved_bf else 0.0
        avg_gn = sum(solved_gn) / len(solved_gn) if solved_gn else 0.0
        rel_red = (avg_bf - avg_gn) / avg_bf * 100 if solved_bf else 0.0

        guided_better = sum(
            1 for r in rows if r[1] and r[3] and r[4] < r[2]
        )
        pct_better = guided_better / len(solved_bf) * 100 if solved_bf else 0.0

        print("\n╭─────────────────────────── SUMMARY ───────────────────────────╮")
        print(f"Problems tested             : {len(rows):>5d}")
        print("")
        print(f"Solved by brute‑force       : {len(solved_bf):>5d}"
              f" (failed on {unsolved_bf:>4d})      ")
        print(f"Solved by GNN‑guided        : {len(solved_gn):>5d}"
              f" (failed on {unsolved_gn:>4d})     ")
        print("")
        if solved_bf:
            print(f"Avg steps (brute)           : {avg_bf:>8.1f}")
        if solved_gn:
            print(f"Avg steps (guided)          : {avg_gn:>8.1f}")
        if solved_bf and solved_gn:
            print(f"Relative reduction          : {rel_red:>7.1f} % ")
            print(f"Guided faster on            : {guided_better:>5d} / "
                  f"{len(solved_bf):<5d} solved  ({pct_better:>5.1f} %) ")

if __name__ == "__main__":
    main()

# python compare_solvers.py --problems Dataset/Test_Res_Pairs_4 --checkpoint Models/gnn_model4.pt --max_args 8
# --predicates Pred1 Pred2 Pred3 --max_args 8

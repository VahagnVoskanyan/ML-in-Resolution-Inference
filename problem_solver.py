import os
import json
import time
from unification_resolution import UnificationResolution

# Load clauses from a JSONL file, ignoring resolvable_pairs and best_pair
def load_clauses_from_jsonl(path):
    with open(path) as f:
        line = f.readline().strip()
        if not line:
            return []
        data = json.loads(line)
    raw = data.get('clauses', [])
    clauses = []
    for entry in raw:
        if isinstance(entry, list) and len(entry) >= 3 and isinstance(entry[2], list):
            lits = entry[2]
        elif isinstance(entry, list):
            lits = entry
        else:
            continue
        clauses.append(set(lits))
    return clauses

def try_subsumption(subsumer_clause, subsumed_clause, ur):
    """
    Try to find a substitution that makes subsumer_clause a subset of subsumed_clause.
    
    Args:
        subsumer_clause: The potentially subsuming clause (list of literals)
        subsumed_clause: The potentially subsumed clause (list of literals)
        ur: UnificationResolution object
        
    Yields:
        Substitution if found, None otherwise
    """
    # Base case: empty subsumer is a subset of anything
    if not subsumer_clause:
        yield {}
        return
        
    # Recursive approach to find a substitution that works for all literals
    def backtrack(subsumer_idx, subsumed_indices, current_subst):
        # Success case: we've matched all literals in subsumer_clause
        if subsumer_idx >= len(subsumer_clause):
            yield current_subst
            return
            
        current_lit = subsumer_clause[subsumer_idx]
        
        # Apply current substitution to the literal
        if current_subst:
            current_lit = ur.apply_subst_to_literal(current_lit, current_subst)
            
        # Try to match with each unused literal in subsumed_clause
        for i in range(len(subsumed_clause)):
            if i in subsumed_indices:
                continue
                
            subsumed_lit = subsumed_clause[i]
            
            # Try unification to see if literals can match
            sign_a, pred_a, _ = ur.parse_literal(current_lit)
            sign_b, pred_b, _ = ur.parse_literal(subsumed_lit)
            
            # Signs and predicates must be the same
            if sign_a != sign_b or pred_a != pred_b:
                continue
                
            # Try to unify the two literals
            new_subst = ur.can_resolve(
                current_lit if sign_a > 0 else current_lit[1:],  # Remove ~ for neg literals
                subsumed_lit if sign_b > 0 else subsumed_lit[1:]  # Remove ~ for neg literals
            )
            
            # If unified, combine substitutions and continue with next literal
            if new_subst is not None:
                # Combine substitutions
                combined_subst = current_subst.copy()
                for var, term in new_subst.items():
                    # Apply current substitution to new terms
                    term = ur.apply_subst_to_term(term, current_subst)
                    combined_subst[var] = term
                    
                # Check if combined substitution is consistent
                is_consistent = True
                for var, term in combined_subst.items():
                    if var in current_subst and current_subst[var] != term:
                        is_consistent = False
                        break
                        
                if is_consistent:
                    # Mark this literal as used and continue
                    subsumed_indices.add(i)
                    yield from backtrack(subsumer_idx + 1, subsumed_indices, combined_subst)
                    subsumed_indices.remove(i)
    
    # Start backtracking with first literal, no used indices, empty substitution
    yield from backtrack(0, set(), {})

def is_subsumed(new_clause, existing_clauses, ur, subsumption_cache):
    """
    Check if a new clause is subsumed by any existing clause.
    A clause A subsumes clause B if there exists a substitution θ such that Aθ ⊆ B.
    
    Args:
        new_clause: The clause to check (as a set of literals)
        existing_clauses: Set of existing clauses (as frozensets of literals)
        ur: UnificationResolution object with unification methods
        
    Returns:
        True if new_clause is subsumed by any existing clause, False otherwise
    """

    fs = frozenset(new_clause)
    if fs in subsumption_cache:
        return subsumption_cache[fs]

    # Convert new_clause to a list for easier iteration
    new_clause_list = list(new_clause)
    result = False
    
    for existing_clause_frozen in existing_clauses:
        existing_clause = list(existing_clause_frozen)
        
        # Skip if existing clause has more literals (can't subsume)
        if len(existing_clause) > len(new_clause_list):
            continue
            
        # Try to find a substitution that makes existing_clause a subset of new_clause
        for substitution in try_subsumption(existing_clause, new_clause_list, ur):
            if substitution is not None:
                result = True
                break
        if result:
            break
                
    subsumption_cache[fs] = result
    return result

def resolution_prover(clauses, max_clause_size=8, timeout_seconds=30, use_subsumption=True):
    """
    Basic resolution prover: tries all clause pairs, applies unification,
    tracks steps until empty clause or exhaustion.
    Enhanced with size limits and subsumption checking, and timeout.
    Returns (proved: bool, steps: int).
    """
    ur = UnificationResolution()
    all_clauses = set(frozenset(c) for c in clauses)
    subsumption_cache: dict[frozenset, bool] = {}
    new_clauses = set()
    processed_pairs = set()
    step_count = 0
    skipped_count = 0
    skipped_subsumption_count = 0
    start_time = time.time()

    while True:
        current_time = time.time()
        if current_time - start_time > timeout_seconds:
            return False, step_count, True  # Return timed_out=True
        
        # Every 1000 steps, check time and print progress
        if step_count % 1000 == 0 and step_count > 0:
            elapsed = current_time - start_time
            print(f"Progress: {step_count} steps, {len(all_clauses)} clauses, {elapsed:.2f} seconds elapsed")

        for c1 in list(all_clauses):
            for c2 in list(all_clauses):
                if c1 == c2:
                    continue
                if repr(c1) >= repr(c2):
                    continue
                pair_key = (c1, c2)
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)

                for litA in c1:
                    for litB in c2:
                        # Check for timeout periodically during intensive loops
                        if step_count > 100 and step_count % 100 == 0:
                            if time.time() - start_time > timeout_seconds:
                                print(f"TIMEOUT after {timeout_seconds} seconds")
                                return False, step_count, True

                        unifier = ur.can_resolve(litA, litB)
                        if unifier is None:
                            continue
                        # build resolvent
                        resolvent = set()
                        for l in c1:
                            if l != litA:
                                resolvent.add(ur.apply_subst_to_literal(l, unifier))
                        for l in c2:
                            if l != litB:
                                resolvent.add(ur.apply_subst_to_literal(l, unifier))

                        step_count += 1

                        if not resolvent:
                            #elapsed = time.time() - start_time
                            #print(f"Proof found in {elapsed:.2f} seconds")
                            return True, step_count, False
                        
                        # Skip overly large clauses to prevent infinite loop
                        if len(resolvent) > max_clause_size:
                            skipped_count += 1
                            continue

                        # Check for subsumption
                        res_fs = frozenset(resolvent)
                        if res_fs in all_clauses or res_fs in new_clauses:
                            continue
                            
                        if use_subsumption and is_subsumed(resolvent, all_clauses, ur, subsumption_cache):
                            skipped_subsumption_count += 1
                            continue
                            
                        new_clauses.add(res_fs)

        if not new_clauses:
            return False, step_count, False
        
        all_clauses |= new_clauses
        new_clauses.clear()


def main():
    jsonl_dir = 'Dataset/Test_Res_Pairs_2'

    max_resolvent_size = 8
    timeout_seconds = 30  # timeout seconds
    use_subsumption = False  # Enable subsumption

    # Check if command-line arguments are provided
    # import sys
    # if len(sys.argv) > 1:
    #     try:
    #         timeout_seconds = int(sys.argv[1])
    #         print(f"Using timeout of {timeout_seconds} seconds")
    #         if len(sys.argv) > 2:
    #             max_clause_size = int(sys.argv[2])
    #             print(f"Using max clause size of {max_clause_size}")
    #     except ValueError:
    #         print("Invalid command line arguments. Usage: python problem_solver.py [timeout_seconds] [max_clause_size]")
    #         return

    if not os.path.isdir(jsonl_dir):
        print(f"Directory '{jsonl_dir}' not found.")
        return
    
    files = [f for f in sorted(os.listdir(jsonl_dir)) if f.endswith('.jsonl')]

    if not files:
        print(f"No .jsonl files in '{jsonl_dir}'.")
        return

    for fn in files:
        path = os.path.join(jsonl_dir, fn)
        clauses = load_clauses_from_jsonl(path)
        if not clauses:
            print(f"{fn}: NO CLAUSES PARSED")
            continue
        try:
            proved, steps, timed_out = resolution_prover(clauses, max_resolvent_size, timeout_seconds, use_subsumption)
            if timed_out:
                status = 'TIMEOUT'
            else:
                status = 'PROVED' if proved else 'NOT PROVED'
            print(f"{fn}: {status} in {steps} resolution steps.")
        except Exception as e:
            print(f"{fn}: ERROR - {str(e)}")

if __name__ == '__main__':
    main()

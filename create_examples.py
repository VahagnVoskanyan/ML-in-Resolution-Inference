import random, math
import numpy as np
import json

from unification_resolution import UnificationResolution
from create_examples_helpers import negate_literal, parse_tptp_clauses, write_to_tptp


def all_resolvents(C1, C2):
    """
    Returns a list [new_clause, ...] — the result of the resolution between C1 and C2.
    We assume that C1 and C2 are sets of literals of the form { L1, L2, ... }.
    We ignore superposition: '=' is treated as an ordinary predicate eq(t1, t2).
    """
    resolvents = []

    resolver = UnificationResolution()
    for litA in C1:
        for litB in C2:
            unifier = resolver.can_resolve(litA, litB)
            if unifier is None:
                continue
                
            # Build the resolvent clause by applying substitutions
            resolvent = set()
            
            # Add literals from clauseA except litA
            for lit in C1:
                if lit != litA:
                    resolvent.add(resolver.apply_subst_to_literal(lit, unifier))
            
            # Add literals from clauseB except litB
            for lit in C2:
                if lit != litB:
                    resolvent.add(resolver.apply_subst_to_literal(lit, unifier))
            
            resolvents.append(resolvent)

    return resolvents

def forward_propose(axioms, N=10, temperature=5.0):
    """
    Generates a linear chain of clauses C0..C_N and returns the last clause C_N.

    :param axioms: a list of triples (name, role, set_of_literals), obtained from parse_tptp_clauses  
    :param N: the number of steps (chain depth)  
    :param temperature: a parameter for softmax-weighting by clause size  
    :return: the final clause (a set of literals), which will serve as the conject
    """
    # Take all axiom clauses (role 'axiom').
    known_clauses = [cl for (_, role, cl) in axioms if role == 'axiom']
    
    # Randomly select the starting clause C0.
    C0 = random.choice(known_clauses)
    chain = [C0]

    for t in range(N):
        candidates = []
        # For each known clause, attempt to resolve chain[-1] with it.
        for c2 in known_clauses:
            cand = all_resolvents(chain[-1], c2)
            candidates.extend(cand)
        
        # If no resolvents are found, the chain is terminated.
        if not candidates:
            break
        
        # Softmax over "size" (number of literals) – the smaller the clause, the higher the selection probability.
        sizes = np.array([len(c) for c in candidates])
        weights = np.exp(-sizes / temperature)
        probs = weights / np.sum(weights)
        idx = np.random.choice(len(candidates), p=probs)
        Cnew = candidates[idx]
        
        chain.append(Cnew)
        known_clauses.append(Cnew)
    
    # Returns the last clause in the chain, which will be our "conjecture".
    return chain[-1]

def negate_clause(clause: set) -> list:
    """
    Inverts a disjunction:
      C = (L1 ∨ L2 ∨ ... )
      ¬C = (¬L1) ∧ (¬L2) ∧ ...
    Returns a list of new TPTP-style clauses, where each is a singleton set containing the negated literal.
    """
    negated_clauses = []
    for L in clause:
        neg_literal = negate_literal(L)
        negated_clauses.append({neg_literal})
    return negated_clauses

def generate_problem(axioms, N=10, T=5.0):
    """
    Generates a single problem: axioms + neg(C_N).  
    Returns a list of clauses (axioms + negated_conjecture).  
    """
    C_final = forward_propose(axioms, N, T)
    negated = negate_clause(C_final)
    
    # Собираем всё вместе
    problem = []
    for (nm,role,cl) in axioms:
        if role=='axiom':
            problem.append((nm, 'axiom', cl))
    i = 0
    for ncl in negated:
        i += 1
        problem.append((f'goal_{i}', 'negated_conjecture', ncl))
    
    return problem

# Example of usage:
# axioms = parse_tptp_clauses('Axioms_clausified/NUM005+1.ax_claused.txt')
# for k in range(1000):
#     prob = generate_problem(axioms, N=10, T=5.0)
#     write_to_tptp(prob, f'gen_problem_{k}.p')

# Example of usage: parse_tptp_clauses(filename)
# if __name__ == '__main__':
#     filePath = 'Axioms_clausified/CAT002-0.ax_claused.txt'
#     cl_list = parse_tptp_clauses(filePath)
#     for cl in cl_list:
#         print(cl)

if __name__ == '__main__':
    fileName = "CAT001-0"
    axioms = parse_tptp_clauses(f'Axioms_clausified/{fileName}.ax_claused.txt')

    for k in range(2000):
        N=50
        T=8.0
        problem = generate_problem(axioms, N, T)

        write_to_tptp(problem, f'Gen_Problems/gen_prob_{fileName}_N={N}_T={T}_{k}.p')
        print(f"Problem created: {fileName}_{k}")

    # Clausify generated problem files
    #from renumber_clause_ids import command
    #import subprocess
    #subprocess.run(command)

    # Parse all clausified problems and find resolvable pairs
    # import os
    # import glob
    # from resolvable_pair_finder_helper import find_candidate_resolvable_pairs
    # for prob_path in glob.glob('Gen_Problems_Copy/*.p'):
    #     clauses = parse_tptp_clauses(prob_path)
    #     resolvable_pairs = find_candidate_resolvable_pairs(clauses)
    #     base = os.path.splitext(os.path.basename(prob_path))[0]
    #     json_filename = f'Res_Pairs/{base}_rs.jsonl'
    #     with open(json_filename, 'w') as fp:
    #         json.dump(resolvable_pairs, fp)
    #     print(f"Wrote {json_filename}")



        # from resolvable_pair_finder_helper import find_candidate_resolvable_pairs
        # resolvable_pairs = find_candidate_resolvable_pairs(problem)

        # json_filename = f'Res_Pairs/gen_prob_{fileName}_N={N}_T={T}_{k}_rs.jsonl'

        # with open(json_filename, "w") as fp:
        #     fp.write(json.dumps(resolvable_pairs) + "\n")
        # print(f"wrote {json_filename}")


        # with open(json_filename, 'w') as fp:
        #     fp.write(json.dumps({"clauses": resolvable_pairs["clauses"]}) + "\n")
        #     for candidate in resolvable_pairs["resolvable_pairs"]:
        #         fp.write(json.dumps(candidate) + "\n")
        #     fp.write(json.dumps({"best_pair": resolvable_pairs["best_pair"]}))
            #json.dump(resolvable_pairs, fp)

        ###
        # from generate_dataset import serializa_clauses
        # ser_clauses = serializa_clauses(problem)

        # json_filename = f'dataset/gen_problem_clauses_{fileName}_N={N}_T={T}_{k}.jsonl'

        # with open(json_filename, 'w') as fp:
        #      json.dump(ser_clauses, fp)
        ###

        # Slows down everything
        #run_comnnads_solve.run_docker_solve_command()


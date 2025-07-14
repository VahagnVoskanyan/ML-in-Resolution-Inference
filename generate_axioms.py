#!/usr/bin/env python3
"""
generate_tptp_axioms.py

Generate a TPTP .ax file containing only axioms (no conjecture or type declarations),
using an integrated ResolutionDataGenerator.
"""

import random
import argparse
from typing import List, Optional

class ResolutionDataGenerator:
    def __init__(
        self,
        predicates: List[str] = None,
        variables: List[str] = None,
        constants: List[str] = None,
        functions: List[str] = None,
        min_clause_length: int = 1,
        max_clause_length: int = 3,
        max_term_arity: int = 3,
        max_function_arity: int = 1
    ):
        """Initialize the clause generator with customizable parameters."""
        self.predicates = predicates or ["pred1", "pred2", "pred3", "pred4", "pred5"]
        self.variables = variables or ["X0", "X1", "X2"]
        self.constants = constants or ["const_a", "const_b", "const_c"]#, "const_d", "const_e"]
        self.functions = functions or ["func_f", "func_g", "func_h"]
        self.min_clause_length = min_clause_length
        self.max_clause_length = max_clause_length
        self.max_term_arity = max_term_arity
        self.max_function_arity = max_function_arity
    
    def generate_term(self, allow_function: bool = True, is_top_level: bool = False) -> str:
        """Generate a random term with careful syntax considerations."""
        if is_top_level:
            # Force variable at top level to avoid type quantification issues
            return random.choice(self.variables)
        
        term_type = random.choice(
            ['variable', 'constant', 'function'] if allow_function else ['variable', 'constant']
        )
        
        if term_type == 'variable':
            return random.choice(self.variables)
        
        if term_type == 'constant':
            return random.choice(self.constants)
        
        # Function generation
        func = random.choice(self.functions)
        arity = random.randint(1, min(self.max_function_arity, len(self.variables)))
        args = [self.generate_term(allow_function=False) for _ in range(arity)]
        return f"{func}({','.join(args)})"
    
    def generate_literal(self, polarity: Optional[bool] = None) -> str:
        """Generate a random literal with syntax considerations."""
        predicate = random.choice(self.predicates)
        arity = random.randint(1, self.max_term_arity)
        
        # Now allow any term type at all positions
        terms = [self.generate_term(allow_function=True) for _ in range(arity)]
        
        # Randomly decide polarity if not specified
        if polarity is None:
            polarity = random.choice([True, False])
        
        literal = f"{predicate}({','.join(terms)})"
        return literal if polarity else f"~{literal}"
    
    def is_tautological_clause(self, clause: List[str]) -> bool:
        """Check if a clause is tautological."""
        for literal in clause:
            negated = literal[1:] if literal.startswith('~') else f"~{literal}"
            if negated in clause:
                return True
        return False
    
    def is_trivial_clause(self, clause: List[str]) -> bool:
        """Check if a clause is trivial."""
        # If all literals are the same, it's trivial
        if len(set(clause)) == 1:
            return True
        
        # A naive check for multiple constants in the same clause
        constants_in_clause = set()
        for literal in clause:
            for c in self.constants:
                if c in literal:
                    constants_in_clause.add(c)
        if len(constants_in_clause) > 1:
            return True
        
        return False
    
    def generate_non_trivial_clause(self, max_attempts: int = 100) -> List[str]:
        """Generate a clause that is neither tautological nor trivial."""
        for _ in range(max_attempts):
            # Choose length between min and max
            num_literals = random.randint(self.min_clause_length, self.max_clause_length)
            clause = [self.generate_literal() for _ in range(num_literals)]
            
            if not (self.is_tautological_clause(clause) or self.is_trivial_clause(clause)):
                return clause
        
        raise RuntimeError("Unable to generate a non-trivial clause after maximum attempts")


def generate_axioms(
    num_axioms: int,
    min_clause_length: int,
    max_clause_length: int,
    max_term_arity: int,
    output_file: str
) -> None:
    """
    Generate `num_axioms` non-trivial clauses and write them as TPTP axioms.

    :param num_axioms: number of axioms (clauses) to generate
    :param max_clause_length: maximum number of literals per clause
    :param max_term_arity: maximum arity for predicate symbols
    :param output_file: path to write the .ax file
    """
    generator = ResolutionDataGenerator(
        min_clause_length=min_clause_length,
        max_clause_length=max_clause_length,
        max_term_arity=max_term_arity
    )
    clauses = []
    while len(clauses) < num_axioms:
        clause = generator.generate_non_trivial_clause()
        clauses.append(clause)

    with open(output_file, 'w') as f:
        for idx, clause in enumerate(clauses, start=1):
            # join literals with TPTP disjunction '|'
            clause_str = ' | '.join(clause)
            f.write(f"fof(ax{idx}, axiom, ({clause_str})).\n")

    print(f"Wrote {num_axioms} axioms to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a TPTP .ax file containing only axioms"
    )
    parser.add_argument(
        '--num-axioms', '-n',
        type=int, default=30,
        help='Number of axioms to generate'
    )
    parser.add_argument(
        '--min-clause-length', '-m',
        type=int, default=2,
        help='Minimum literals per clause'
    )
    parser.add_argument(
        '--max-clause-length', '-c',
        type=int, default=5,
        help='Maximum literals per clause'
    )
    parser.add_argument(
        '--max-term-arity', '-a',
        type=int, default=3,
        help='Maximum predicate arity'
    )
    parser.add_argument(
        '--output-file', '-o',
        type=str, default='Axioms/gen_ax_file_7.ax',
        help='Output .ax file name'
    )
    args = parser.parse_args()

    generate_axioms(
        num_axioms=args.num_axioms,
        min_clause_length=args.min_clause_length,
        max_clause_length=args.max_clause_length,
        max_term_arity=args.max_term_arity,
        output_file=args.output_file
    )

if __name__ == '__main__':
    main()

# python generate_axioms.py -n 20 -m 2 -c 5 -a 3 -o Axioms/gen_ax_file_7.ax
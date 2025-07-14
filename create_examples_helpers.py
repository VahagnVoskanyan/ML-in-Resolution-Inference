import re

from unification_resolution import UnificationResolution

def parse_tptp_clauses(filePath):
    """
    A simple TPTP parser for axiom clauses.
    Returns a list of triples (name, role, set_of_literals).
    Each literal is represented as a string.
    """
    clauses = []
    with open(filePath, 'r') as f:
        # Read the entire file and remove comments (starting with %)
        content = f.read()
    # Remove comment lines
    content = "\n".join(line for line in content.splitlines() if not line.strip().startswith('%'))
    
    # Since each clause ends with ").", we use a regex to find all such constructs.
    # Approximate format: cnf(u65,axiom, ... ). (with possible line breaks)
    pattern = r'cnf\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,(.*?)\)\s*\.'
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for m in matches:
        name = m.group(1).strip()
        role = m.group(2).strip()
        formula = m.group(3).strip()
        
        # If the formula is enclosed in outer parentheses, remove them.
        if formula.startswith('(') and formula.endswith(')'):
            formula = formula[1:-1].strip()
        
        # Split the formula by the '|' character to get the literals.
        # Here we assume the disjunction operator does not occur inside literals.
        literals = [lit.strip() for lit in formula.split('|') if lit.strip()]
        # Convert to a set (or can keep as a list if multiplicity matters)
        literal_set = set(literals)
        
        clauses.append((name, role, literal_set))
        #print(clauses[-1])
    
    return clauses

def negate_literal(literal: str) -> str:
    """
    Negate a literal:
    - For non-equality predicates: if the literal is positive, add '~'; if it's negative (starts with '~'),
      remove the '~'.
    - For equality, if literal is positive (format "X = Y"), produce negative form ("X != Y"), and vice versa.
    """
    resolver = UnificationResolution()
    sign, pred, args = resolver.parse_literal(literal)
    if pred == "eq":
        if sign > 0:
            # Positive equality becomes inequality.
            return f"{args[0]} != {args[1]}"
        else:
            # Negative equality becomes positive equality.
            return f"{args[0]} = {args[1]}"
    else:
        if sign > 0:
            # Positive literal: add a negation.
            if args:
                return f"~{pred}({','.join(args)})"
            else:
                return f"~{pred}"
        else:
            # Negative literal: remove the negation.
            if args:
                return f"{pred}({','.join(args)})"
            else:
                return pred

def write_to_tptp(clauses, filePath):
    """
    Converts a list of clauses in the internal representation (tuples: (name, role, clause))
    to a TPTP-formatted file.

    Each clause is written as:
      cnf(name, role, (L1 | L2 | ... )).
    """
    with open(filePath, 'w') as f:
        for name, role, clause in clauses:
            # Join literals with disjunction
            # Sorting is optional but can make the output consistent.
            disjunction = " | ".join(sorted(clause))
            line = f"cnf({name}, {role}, ({disjunction})).\n"
            f.write(line)
        

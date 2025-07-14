cnf(u1, axiom, (product(X0,X1,compose(X0,X1)) | ~defined(X0,X1))).
cnf(u2, axiom, (defined(X0,X1) | ~product(X0,X1,X2))).
cnf(u3, axiom, (defined(X1,X2) | ~defined(X3,X2) | ~product(X0,X1,X3))).
cnf(u4, axiom, (defined(X0,X4) | ~defined(X3,X2) | ~product(X0,X1,X3) | ~product(X1,X2,X4))).
cnf(u5, axiom, (product(X0,X4,X5) | ~product(X0,X1,X3) | ~product(X1,X2,X4) | ~product(X3,X2,X5))).
cnf(u6, axiom, (defined(X0,X1) | ~defined(X0,X4) | ~product(X1,X2,X4))).
cnf(u7, axiom, (defined(X3,X2) | ~defined(X0,X4) | ~product(X0,X1,X3) | ~product(X1,X2,X4))).
cnf(u8, axiom, (product(X3,X2,X5) | ~product(X0,X1,X3) | ~product(X0,X4,X5) | ~product(X1,X2,X4))).
cnf(u9, axiom, (defined(X0,X2) | ~defined(X0,X1) | ~defined(X1,X2) | ~identity_map(X1))).
cnf(u10, axiom, (identity_map(domain(X0)))).
cnf(u11, axiom, (identity_map(codomain(X0)))).
cnf(u12, axiom, (defined(X0,domain(X0)))).
cnf(u13, axiom, (defined(codomain(X0),X0))).
cnf(u14, axiom, (product(X0,domain(X0),X0))).
cnf(u15, axiom, (product(codomain(X0),X0,X0))).
cnf(u16, axiom, (product(X0,X1,X1) | ~defined(X0,X1) | ~identity_map(X0))).
cnf(u17, axiom, (product(X0,X1,X0) | ~defined(X0,X1) | ~identity_map(X1))).
cnf(u18, axiom, (X2 = X6 | ~product(X0,X1,X2) | ~product(X0,X1,X6))).
cnf(goal_1, negated_conjecture, (product(X0,X0,X0))).
cnf(goal_2, negated_conjecture, (defined(X0,X0))).
cnf(goal_3, negated_conjecture, (product(codomain(X0),X0,codomain(X0)))).
cnf(goal_4, negated_conjecture, (product(X0,X0,codomain(X0)))).
cnf(goal_5, negated_conjecture, (~product(codomain(X0),X0,compose(X0,X1)))).
cnf(goal_6, negated_conjecture, (product(X0,X0,domain(X0)))).
cnf(goal_7, negated_conjecture, (identity_map(X0))).

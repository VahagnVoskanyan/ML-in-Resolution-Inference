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
cnf(goal_1, negated_conjecture, (product(X4,X4,domain(codomain(X4))))).
cnf(goal_2, negated_conjecture, (product(X4,X2,X4))).
cnf(goal_3, negated_conjecture, (identity_map(domain(X4)))).
cnf(goal_4, negated_conjecture, (defined(X4,domain(X4)))).
cnf(goal_5, negated_conjecture, (product(domain(codomain(X4)),domain(codomain(X4)),domain(codomain(X4))))).
cnf(goal_6, negated_conjecture, (product(codomain(X4),domain(codomain(X4)),domain(domain(codomain(X4)))))).
cnf(goal_7, negated_conjecture, (identity_map(codomain(X4)))).
cnf(goal_8, negated_conjecture, (product(domain(domain(codomain(X4))),X4,X3))).
cnf(goal_9, negated_conjecture, (product(X4,codomain(X4),codomain(X4)))).
cnf(goal_10, negated_conjecture, (product(domain(domain(codomain(X4))),domain(codomain(X4)),X4))).
cnf(goal_11, negated_conjecture, (product(codomain(X4),domain(codomain(X4)),domain(codomain(X4))))).
cnf(goal_12, negated_conjecture, (identity_map(domain(domain(codomain(X4)))))).
cnf(goal_13, negated_conjecture, (defined(X3,X2))).
cnf(goal_14, negated_conjecture, (product(domain(domain(codomain(X4))),X4,X4))).
cnf(goal_15, negated_conjecture, (product(domain(domain(codomain(X4))),domain(codomain(X4)),domain(codomain(X4))))).
cnf(goal_16, negated_conjecture, (defined(codomain(X4),X4))).
cnf(goal_17, negated_conjecture, (identity_map(domain(codomain(X4))))).
cnf(goal_18, negated_conjecture, (defined(X4,codomain(X4)))).
cnf(goal_19, negated_conjecture, (identity_map(X4))).
cnf(goal_20, negated_conjecture, (defined(X4,X4))).
cnf(goal_21, negated_conjecture, (defined(domain(codomain(X4)),X4))).
cnf(goal_22, negated_conjecture, (product(domain(X4),X4,domain(X4)))).
cnf(goal_23, negated_conjecture, (product(domain(codomain(X4)),domain(domain(codomain(X4))),domain(domain(codomain(X4)))))).
cnf(goal_24, negated_conjecture, (product(X4,domain(codomain(X4)),X4))).
cnf(goal_25, negated_conjecture, (defined(X4,domain(codomain(X4))))).
cnf(goal_26, negated_conjecture, (product(X4,domain(X4),domain(X4)))).
cnf(goal_27, negated_conjecture, (product(domain(codomain(X4)),codomain(X4),domain(codomain(X4))))).
cnf(goal_28, negated_conjecture, (~product(domain(codomain(X4)),domain(codomain(X4)),compose(X0,X1)))).
cnf(goal_29, negated_conjecture, (product(X4,X4,codomain(X4)))).
cnf(goal_30, negated_conjecture, (product(X4,X4,domain(domain(codomain(X4)))))).
cnf(goal_31, negated_conjecture, (product(codomain(X4),codomain(X4),codomain(X4)))).
cnf(goal_32, negated_conjecture, (defined(domain(X4),X4))).

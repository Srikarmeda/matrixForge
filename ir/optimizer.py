# ir/optimizer.py
from ir.tac_generator import Quadruple

class OptimizationResult:
    def __init__(self, optimized_quads, before_count, after_count):
        self.optimized_quads = optimized_quads
        self.before_count = before_count
        self.after_count = after_count
        self.reduction_pct = 0.0
        if before_count > 0:
            self.reduction_pct = round(((before_count - after_count) / before_count) * 100, 1)

def optimize(quads):
    """
    Executes multi-pass optimizations matching the Phase 2 specification:
    1. Literal Buffer Folding (ALLOC_MAT + LOAD_LIT + ASSIGN -> LOAD_LIT direct)
    2. Algebraic Double Negation Cancellation (-(-C) -> C)
    3. Intermediate Temporary Forwarding & Dead Code Elimination (DCE)
    """
    original_count = len(quads)

    # -------------------------------------------------------------
    # PASS 1: Fold Literal Allocations into Direct Loads
    # (ALLOC_MAT -> LOAD_LIT -> ASSIGN) ==> LOAD_LIT directly to var
    # -------------------------------------------------------------
    pass1_quads = []
    i = 0
    while i < len(quads):
        q1 = quads[i]
        if q1.op == "ALLOC_MAT" and i + 2 < len(quads):
            q2 = quads[i + 1]
            q3 = quads[i + 2]
            if (q2.op == "LOAD_LIT" and q2.result == q1.result and 
                q3.op == "ASSIGN" and q3.arg1 == q1.result):
                pass1_quads.append(Quadruple("LOAD_LIT", q2.arg1, None, q3.result, q2.dim_meta))
                i += 3
                continue
        pass1_quads.append(q1)
        i += 1

    # -------------------------------------------------------------
    # PASS 2: Algebraic Double Negation Elimination (-(-C) -> C)
    # Detects: MAT_NEG C -> t4, MAT_NEG t4 -> t5, ASSIGN t5 -> D
    # Replaces directly with: ASSIGN C -> D
    # -------------------------------------------------------------
    pass2_quads = []
    i = 0
    while i < len(pass1_quads):
        q1 = pass1_quads[i]
        if q1.op == "MAT_NEG" and i + 2 < len(pass1_quads):
            q2 = pass1_quads[i + 1]
            q3 = pass1_quads[i + 2]
            if (q2.op == "MAT_NEG" and q2.arg1 == q1.result and
                q3.op == "ASSIGN" and q3.arg1 == q2.result):
                # Double negation detected on original operand q1.arg1
                pass2_quads.append(Quadruple("ASSIGN", q1.arg1, None, q3.result))
                i += 3
                continue
        pass2_quads.append(q1)
        i += 1

    # -------------------------------------------------------------
    # PASS 3: Intermediate Temporary Forwarding / Copy Propagation
    # Eliminates temporary result registers immediately consumed by ASSIGN:
    # MAT_MUL t2, B, t3  +  ASSIGN t3, None, C  ==>  MAT_MUL t2, B, C
    # -------------------------------------------------------------
    pass3_quads = []
    i = 0
    while i < len(pass2_quads):
        curr = pass2_quads[i]
        if (curr.op in ("MAT_MUL", "MAT_ADD", "MAT_SUB") and 
            str(curr.result).startswith("t") and 
            i + 1 < len(pass2_quads)):
            nxt = pass2_quads[i + 1]
            if nxt.op == "ASSIGN" and nxt.arg1 == curr.result:
                # Forward destination directly into user variable
                pass3_quads.append(Quadruple(curr.op, curr.arg1, curr.arg2, nxt.result, curr.dim_meta))
                i += 2
                continue
        pass3_quads.append(curr)
        i += 1

    return OptimizationResult(pass3_quads, original_count, len(pass3_quads))
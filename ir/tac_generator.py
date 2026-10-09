# ir/tac_generator.py
import core.ast_nodes as ast

class Quadruple:
    """Represents a standard Three-Address Code instruction."""
    def __init__(self, op, arg1, arg2, result, dim_meta=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.dim_meta = dim_meta

    def __repr__(self):
        a1 = self.arg1 if self.arg1 is not None else "None"
        a2 = self.arg2 if self.arg2 is not None else "None"
        res = self.result if self.result is not None else "None"
        return f"({self.op:<10}, {str(a1):<10}, {str(a2):<10}, {str(res):<10})"

class TACGenerator:
    def __init__(self, symbol_table):
        self.quads = []
        self.temp_count = 0
        self.symtab = symbol_table

    def new_temp(self):
        """Generates a deterministic temporary variable (t0, t1, ...)."""
        t = f"t{self.temp_count}"
        self.temp_count += 1
        return t

    def generate(self, node):
        """Entry point for AST lowering."""
        self.visit(node)
        return self.quads

    def visit(self, node):
        if node is None:
            return None
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        pass

    def visit_Program(self, node: ast.Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Assignment(self, node: ast.Assignment):
        target_name = node.target.name
        val_addr = self.visit(node.value)
        self.quads.append(Quadruple("ASSIGN", val_addr, None, target_name))
        return target_name

    def visit_MatrixLiteral(self, node: ast.MatrixLiteral):
        rows = len(node.rows)
        cols = len(node.rows[0]) if rows > 0 else 0
        temp = self.new_temp()
        
        # 1. Allocate Matrix Buffer
        self.quads.append(Quadruple("ALLOC_MAT", rows, cols, temp))
        
        # 2. Extract actual numeric grid for backend execution
        numeric_grid = []
        for r in node.rows:
            numeric_grid.append([float(elem.value) for elem in r])
            
        self.quads.append(Quadruple("LOAD_LIT", numeric_grid, None, temp, dim_meta=(rows, cols)))
        return temp

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand_addr = self.visit(node.operand)
        temp = self.new_temp()
        
        if node.op == '-':
            self.quads.append(Quadruple("MAT_NEG", operand_addr, None, temp))
        return temp

    def visit_BinOp(self, node: ast.BinOp):
        left_addr = self.visit(node.left)
        right_addr = self.visit(node.right)
        temp = self.new_temp()
        
        op_map = {
            '+': "MAT_ADD",
            '-': "MAT_SUB",
            '*': "MAT_MUL"
        }
        opcode = op_map.get(node.op, "UNKNOWN_OP")
        self.quads.append(Quadruple(opcode, left_addr, right_addr, temp))
        return temp

    def visit_Identifier(self, node: ast.Identifier):
        return node.name

    def visit_Number(self, node: ast.Number):
        temp = self.new_temp()
        self.quads.append(Quadruple("LOAD_SCALAR", node.value, None, temp))
        return temp

    def visit_PrintStmt(self, node: ast.PrintStmt):
        expr_addr = self.visit(node.expression)
        self.quads.append(Quadruple("PRINT", expr_addr, None, None))

def generate(ast_tree, symbol_table):
    generator = TACGenerator(symbol_table)
    return generator.generate(ast_tree)
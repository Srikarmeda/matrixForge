# semantics/analyzer.py
import core.ast_nodes as ast

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def declare(self, name, var_type, dimensions=None):
        if name in self.symbols:
            raise Exception(f"Semantic Error: Variable '{name}' is already declared.")
        self.symbols[name] = {'type': var_type, 'dimensions': dimensions}

    def lookup(self, name):
        if name not in self.symbols:
            raise Exception(f"Semantic Error: Variable '{name}' is undeclared.")
        return self.symbols[name]


class SemanticAnalyzer:
    def __init__(self):
        self.symtab = SymbolTable()

    def visit(self, node):
        method_name = 'visit_' + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"No semantic rule defined for {type(node).__name__}")

    def visit_Program(self, node):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_Assignment(self, node):
        val_type, dims = self.visit(node.value)
        var_name = node.target.name
        self.symtab.declare(var_name, val_type, dims)
        dim_str = f"{dims[0]}x{dims[1]}" if dims else "scalar"
        print(f"[Symbol Table] Registered '{var_name}' as {val_type} ({dim_str})")

    def visit_MatrixLiteral(self, node):
        rows = len(node.rows)
        cols = len(node.rows[0]) if rows > 0 else 0
        
        # Check for ragged rows
        for r in node.rows:
            if len(r) != cols:
                raise Exception("Semantic Error: Inconsistent matrix row lengths (ragged matrix).")
        return 'matrix', (rows, cols)

    def visit_BinOp(self, node):
        type_l, dims_l = self.visit(node.left)
        type_r, dims_r = self.visit(node.right)

        # 1. Matrix operations
        if type_l == 'matrix' and type_r == 'matrix':
            if node.op in ('+', '-'):
                if dims_l != dims_r:
                    raise Exception(
                        f"Semantic Error: Cannot {node.op} matrices of shape {dims_l} and {dims_r}."
                    )
                return 'matrix', dims_l

            elif node.op == '*':
                # Inner dimensions must match: (m x k) * (k x n) = (m x n)
                if dims_l[1] != dims_r[0]:
                    raise Exception(
                        f"Semantic Error: Dimension mismatch for multiplication: "
                        f"{dims_l[0]}x{dims_l[1]} vs {dims_r[0]}x{dims_r[1]}."
                    )
                return 'matrix', (dims_l[0], dims_r[1])

            elif node.op == '/':
                raise Exception("Semantic Error: Matrix division is undefined. Use inverse multiplication.")

        # 2. Scalar operations
        elif type_l in ('int', 'float') and type_r in ('int', 'float'):
            result_type = 'float' if 'float' in (type_l, type_r) else 'int'
            return result_type, None

        # 3. Scalar-Matrix operations
        elif (type_l == 'matrix' and type_r in ('int', 'float')) or \
             (type_r == 'matrix' and type_l in ('int', 'float')):
            matrix_dims = dims_l if type_l == 'matrix' else dims_r
            if node.op in ('*', '/'):
                return 'matrix', matrix_dims
            raise Exception(f"Semantic Error: Operator '{node.op}' not supported between matrix and scalar.")

        raise Exception(f"Semantic Error: Invalid operand types for '{node.op}': {type_l} and {type_r}.")

    def visit_PrintStmt(self, node):
        self.visit(node.expression)

    def visit_Identifier(self, node):
        sym = self.symtab.lookup(node.name)
        return sym['type'], sym['dimensions']

    def visit_Number(self, node):
        return ('float', None) if isinstance(node.value, float) else ('int', None)


# --- Verification Test ---
if __name__ == '__main__':
    from core.lexer import lexer
    from core.parser import parser

    # Valid multiplication: A(2x3) * B(3x2) -> C(2x2)
    valid_test = '''
    matrix A = [[1, 2, 3], [4, 5, 6]];
    matrix B = [[1, 2], [3, 4], [5, 6]];
    matrix C = A * B;
    print(C);
    '''
    print("--- Testing Valid Matrix Multiplication ---")
    tree = parser.parse(valid_test, lexer=lexer)
    analyzer = SemanticAnalyzer()
    analyzer.visit(tree)
    print("Test passed successfully!\n")

    # Incompatible multiplication: A(2x3) * D(2x2) -> Exception
    invalid_test = '''
    matrix A = [[1, 2, 3], [4, 5, 6]];
    matrix D = [[1, 2], [3, 4]];
    matrix E = A * D;
    '''
    print("--- Testing Incompatible Matrix Multiplication ---")
    try:
        tree = parser.parse(invalid_test, lexer=lexer)
        SemanticAnalyzer().visit(tree)
    except Exception as err:
        print(f"Caught expected compiler failure: {err}")
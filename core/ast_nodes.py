# core/ast_nodes.py

class ASTNode:
    """Base class for all AST nodes."""
    pass

class Program(ASTNode):
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self):
        return f"Program({self.statements})"

class Assignment(ASTNode):
    def __init__(self, target, value):
        self.target = target
        self.value = value
    def __repr__(self):
        return f"Assign({self.target} = {self.value})"

class PrintStmt(ASTNode):
    def __init__(self, expression):
        self.expression = expression
    def __repr__(self):
        return f"Print({self.expression})"

class MatrixLiteral(ASTNode):
    def __init__(self, rows):
        self.rows = rows  # List of lists
    def __repr__(self):
        return f"Matrix({self.rows})"

class BinOp(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"ID({self.name})"

class Number(ASTNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"Num({self.value})"
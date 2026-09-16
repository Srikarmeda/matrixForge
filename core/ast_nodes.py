# core/ast_nodes.py
from dataclasses import dataclass
from typing import List, Union

class ASTNode:
    """Base class for all Abstract Syntax Tree nodes."""
    pass

@dataclass
class Program(ASTNode):
    statements: List[ASTNode]
    lineno: int = 1
    lexpos: int = 0

@dataclass
class Assignment(ASTNode):
    target: 'Identifier'
    value: ASTNode
    lineno: int = 1
    lexpos: int = 0

@dataclass
class PrintStmt(ASTNode):
    expression: ASTNode
    lineno: int = 1
    lexpos: int = 0

@dataclass
class BinOp(ASTNode):
    left: ASTNode
    op: str
    right: ASTNode
    lineno: int = 1
    lexpos: int = 0

@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: ASTNode
    lineno: int = 1
    lexpos: int = 0

@dataclass
class MatrixLiteral(ASTNode):
    rows: List[List[ASTNode]]
    lineno: int = 1
    lexpos: int = 0

@dataclass
class Identifier(ASTNode):
    name: str
    lineno: int = 1
    lexpos: int = 0

@dataclass
class Number(ASTNode):
    value: Union[int, float]
    lineno: int = 1
    lexpos: int = 0
# semantics/analyzer.py
import re
import core.ast_nodes as ast

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self, name, var_type, dimensions=None):
        self.symbols[name] = {
            "type": var_type,
            "dimensions": dimensions
        }

    def lookup(self, name):
        return self.symbols.get(name, None)

    def exists(self, name):
        return name in self.symbols

    def clear(self):
        self.symbols.clear()


class SemanticAnalyzer:
    def __init__(self):
        self.symtab = SymbolTable()
        self.errors = []
        self.source_code = ""
        self.current_stmt = None

    def reset(self, source_code=""):
        self.symtab.clear()
        self.errors = []
        self.source_code = source_code
        self.current_stmt = None

    def _find_line_in_source(self, target_str):
        """Fallback scanner to pinpoint line/col from raw source text."""
        if not self.source_code or not target_str:
            return 1, 1
        lines = self.source_code.splitlines()
        for idx, line in enumerate(lines):
            if target_str in line:
                col = line.find(target_str) + 1
                return idx + 1, col
        return 1, 1

    def add_error(self, message, node=None, offending="", suggestion="", line=None, col=None):
        found_line = line
        found_col = col

        # 1. Try reading from the node
        if found_line is None and node is not None:
            found_line = getattr(node, 'lineno', None)
            lexpos = getattr(node, 'lexpos', None)
            if lexpos is not None and self.source_code:
                line_start = self.source_code.rfind('\n', 0, lexpos) + 1
                found_col = (lexpos - line_start) + 1

        # 2. Try reading from the active statement
        if (found_line is None or found_line <= 1) and self.current_stmt is not None:
            stmt_line = getattr(self.current_stmt, 'lineno', None)
            if stmt_line and stmt_line > 1:
                found_line = stmt_line
                stmt_pos = getattr(self.current_stmt, 'lexpos', None)
                if stmt_pos is not None and self.source_code:
                    line_start = self.source_code.rfind('\n', 0, stmt_pos) + 1
                    found_col = (stmt_pos - line_start) + 1

        # 3. Fallback: Search source code directly for offending token/variable
        if found_line is None or found_line <= 1:
            search_str = offending
            if not search_str and self.current_stmt:
                target_obj = getattr(self.current_stmt, 'target', None)
                if target_obj:
                    search_str = getattr(target_obj, 'name', '')
            f_line, f_col = self._find_line_in_source(search_str)
            if f_line > 1:
                found_line, found_col = f_line, f_col

        final_line = found_line if (isinstance(found_line, int) and found_line >= 1) else 1
        final_col = found_col if (isinstance(found_col, int) and found_col >= 1) else 1

        err = {
            "type": "Semantic Error",
            "message": message,
            "line": final_line,
            "col": final_col,
            "offending": offending,
            "suggestion": suggestion
        }
        self.errors.append(err)

    def visit(self, node):
        if node is None:
            return None
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        self.add_error(
            message=f"No semantic visitor defined for node type '{type(node).__name__}'",
            node=node,
            suggestion="Verify that the AST node structure is recognized by the compiler."
        )
        return {"type": "error", "dimensions": None}

    # 1. Program & Statements

    def visit_Program(self, node: ast.Program):
        for stmt in node.statements:
            self.current_stmt = stmt
            self.visit(stmt)
        return None

    def visit_Assignment(self, node: ast.Assignment):
        self.current_stmt = node
        target_name = node.target.name
        val_info = self.visit(node.value)

        if val_info and val_info.get("type") != "error":
            self.symtab.define(
                name=target_name,
                var_type=val_info.get("type"),
                dimensions=val_info.get("dimensions")
            )
        else:
            self.symtab.define(
                name=target_name,
                var_type="unknown",
                dimensions=None
            )
        return None

    def visit_PrintStmt(self, node: ast.PrintStmt):
        self.current_stmt = node
        self.visit(node.expression)
        return None

    # 2. Unary Operations

    def visit_UnaryOp(self, node: ast.UnaryOp):
        operand_info = self.visit(node.operand)

        if not operand_info or operand_info.get("type") == "error":
            return {"type": "error", "dimensions": None}

        if node.op == '-':
            if operand_info["type"] in ("matrix", "scalar"):
                return {
                    "type": operand_info["type"],
                    "dimensions": operand_info["dimensions"]
                }
            else:
                self.add_error(
                    message=f"Unary operator '-' not supported for data type '{operand_info.get('type')}'",
                    node=node,
                    offending="-",
                    suggestion="Unary negation can only be applied to scalar numbers or matrices."
                )
                return {"type": "error", "dimensions": None}
        elif node.op == '+':
            return operand_info
        else:
            self.add_error(
                message=f"Unsupported unary operator '{node.op}'",
                node=node,
                offending=node.op,
                suggestion="Supported unary operators are '+' and '-'."
            )
            return {"type": "error", "dimensions": None}

    # 3. Binary Operations

    def visit_BinOp(self, node: ast.BinOp):
        left_info = self.visit(node.left)
        right_info = self.visit(node.right)

        if not left_info or not right_info or left_info.get("type") == "error" or right_info.get("type") == "error":
            return {"type": "error", "dimensions": None}

        op = node.op

        if op in ('+', '-'):
            if left_info["type"] == "matrix" and right_info["type"] == "matrix":
                dim_l = left_info["dimensions"]
                dim_r = right_info["dimensions"]

                if dim_l != dim_r:
                    self.add_error(
                        message=f"Dimension mismatch for {op}: {dim_l[0]}x{dim_l[1]} vs {dim_r[0]}x{dim_r[1]}",
                        node=node,
                        offending=op,
                        suggestion=f"Matrices must have identical row and column dimensions for element-wise '{op}'."
                    )
                    return {"type": "error", "dimensions": None}
                return {"type": "matrix", "dimensions": dim_l}

            elif left_info["type"] == "scalar" and right_info["type"] == "scalar":
                return {"type": "scalar", "dimensions": None}

            elif (left_info["type"] == "matrix" and right_info["type"] == "scalar") or \
                 (left_info["type"] == "scalar" and right_info["type"] == "matrix"):
                target_dim = left_info["dimensions"] if left_info["type"] == "matrix" else right_info["dimensions"]
                return {"type": "matrix", "dimensions": target_dim}

        elif op == '*':
            if left_info["type"] == "matrix" and right_info["type"] == "matrix":
                dim_l = left_info["dimensions"]
                dim_r = right_info["dimensions"]

                if dim_l[1] != dim_r[0]:
                    self.add_error(
                        message=f"Dimension mismatch for multiplication: {dim_l[0]}x{dim_l[1]} vs {dim_r[0]}x{dim_r[1]}",
                        node=node,
                        offending="*",
                        suggestion="Inner dimensions must match: columns of Matrix A must equal rows of Matrix B (cols(A) == rows(B))."
                    )
                    return {"type": "error", "dimensions": None}
                return {"type": "matrix", "dimensions": (dim_l[0], dim_r[1])}

            elif left_info["type"] == "matrix" and right_info["type"] == "scalar":
                return {"type": "matrix", "dimensions": left_info["dimensions"]}

            elif left_info["type"] == "scalar" and right_info["type"] == "matrix":
                return {"type": "matrix", "dimensions": right_info["dimensions"]}

            elif left_info["type"] == "scalar" and right_info["type"] == "scalar":
                return {"type": "scalar", "dimensions": None}

        elif op == '/':
            if left_info["type"] == "matrix" and right_info["type"] == "scalar":
                return {"type": "matrix", "dimensions": left_info["dimensions"]}

            elif left_info["type"] == "scalar" and right_info["type"] == "scalar":
                return {"type": "scalar", "dimensions": None}

            elif left_info["type"] == "matrix" and right_info["type"] == "matrix":
                self.add_error(
                    message="Direct matrix division '/' is mathematically undefined",
                    node=node,
                    offending="/",
                    suggestion="Direct matrix division is not supported. Use matrix multiplication with inverse instead."
                )
                return {"type": "error", "dimensions": None}

        self.add_error(
            message=f"Operator '{op}' is not supported between types '{left_info['type']}' and '{right_info['type']}'",
            node=node,
            offending=op,
            suggestion="Verify data types and dimension compatibility for this operation."
        )
        return {"type": "error", "dimensions": None}

    # 4. Matrix Literals

    def visit_MatrixLiteral(self, node: ast.MatrixLiteral):
        num_rows = len(node.rows)
        if num_rows == 0:
            self.add_error(
                message="Empty matrix literal '[]' is not permitted",
                node=node,
                offending="[]",
                suggestion="Define at least one row containing numeric values."
            )
            return {"type": "error", "dimensions": None}

        row_lengths = [len(r) for r in node.rows]
        first_col_len = row_lengths[0]

        if first_col_len == 0:
            self.add_error(
                message="Matrix row contains 0 column elements",
                node=node,
                offending="[]",
                suggestion="Ensure each matrix row contains at least one numeric value."
            )
            return {"type": "error", "dimensions": None}

        if any(length != first_col_len for length in row_lengths):
            # Target the identifier being assigned to, or fallback to '['
            target_name = getattr(getattr(self.current_stmt, 'target', None), 'name', '[')
            self.add_error(
                message=f"Ragged matrix detected: Inconsistent row lengths {row_lengths}",
                node=node,
                offending=target_name,
                suggestion="All rows in a matrix literal must contain the exact same number of column elements."
            )
            return {"type": "error", "dimensions": None}

        for row in node.rows:
            for elem in row:
                elem_info = self.visit(elem)
                if elem_info and elem_info.get("type") == "error":
                    return {"type": "error", "dimensions": None}

        return {"type": "matrix", "dimensions": (num_rows, first_col_len)}

    # 5. Identifiers & Numbers

    def visit_Identifier(self, node: ast.Identifier):
        entry = self.symtab.lookup(node.name)
        if entry is None:
            self.add_error(
                message=f"Variable '{node.name}' is undeclared",
                node=node,
                offending=node.name,
                suggestion=f"Declare variable '{node.name}' with 'matrix {node.name} = ...' before referencing it."
            )
            return {"type": "error", "dimensions": None}
        return entry

    def visit_Number(self, node: ast.Number):
        return {"type": "scalar", "dimensions": None}
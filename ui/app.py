# ui/app.py
import streamlit as st
import pandas as pd
from core.lexer import lexer
from core.parser import parser
import core.ast_nodes as ast
from semantics.analyzer import SemanticAnalyzer

st.set_page_config(page_title="matrixForge Phase 1 Dashboard", layout="wide")

# --- AST to Graphviz DOT Converter ---
def generate_dot(node):
    dot = [
        "digraph AST {",
        '  node [shape=box, style="rounded,filled", fillcolor="#EBF3FB", color="#3182CE", fontname="Courier"];'
    ]
    counter = [0]

    def walk(curr, parent_id=None, edge_label=""):
        cid = f"node_{counter[0]}"
        counter[0] += 1

        if isinstance(curr, ast.Program):
            label = "Program"
        elif isinstance(curr, ast.Assignment):
            label = f"Assign: {curr.target.name}"
        elif isinstance(curr, ast.BinOp):
            label = f"BinOp: {curr.op}"
        elif isinstance(curr, ast.MatrixLiteral):
            rows = len(curr.rows)
            cols = len(curr.rows[0]) if rows else 0
            label = f"Matrix [{rows}x{cols}]"
        elif isinstance(curr, ast.Identifier):
            label = f"ID: {curr.name}"
        elif isinstance(curr, ast.Number):
            label = f"Num: {curr.value}"
        elif isinstance(curr, ast.PrintStmt):
            label = "Print"
        else:
            label = type(curr).__name__

        dot.append(f'  {cid} [label="{label}"];')
        if parent_id is not None:
            lbl_part = f' [label="{edge_label}"]' if edge_label else ""
            dot.append(f'  {parent_id} -> {cid}{lbl_part};')

        if isinstance(curr, ast.Program):
            for stmt in curr.statements:
                walk(stmt, cid)
        elif isinstance(curr, ast.Assignment):
            walk(curr.value, cid, "value")
        elif isinstance(curr, ast.BinOp):
            walk(curr.left, cid, "left")
            walk(curr.right, cid, "right")
        elif isinstance(curr, ast.PrintStmt):
            walk(curr.expression, cid, "expr")
        elif isinstance(curr, ast.MatrixLiteral):
            for r_idx, row in enumerate(curr.rows):
                r_id = f"row_{counter[0]}"
                counter[0] += 1
                dot.append(f'  {r_id} [shape=ellipse, fillcolor="#FEFCBF", color="#D69E2E", label="Row {r_idx}"];')
                dot.append(f'  {cid} -> {r_id};')
                for elem in row:
                    walk(elem, r_id)

    walk(node)
    dot.append("}")
    return "\n".join(dot)

# --- Main Layout ---
st.title("matrixForge - Phase 1 Visualizer")
st.caption("Pipeline: Lexical Analysis → Syntax Analysis (AST) → Semantic Analysis & Symbol Table")

default_code = """matrix A = [[1, 2, 3], [4, 5, 6]];
matrix B = [[1, 2], [3, 4], [5, 6]];
matrix C = A * B;
print(C);"""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Source Input")
    code_input = st.text_area("Input matrixForge code:", default_code, height=220)
    compile_btn = st.button("Analyze Code", type="primary")

token_records = []
tree = None
parse_error = None
semantic_error = None
analyzer = SemanticAnalyzer()

if compile_btn or code_input:
    # 1. Lexical Analysis
    lexer.lineno = 1
    lexer.input(code_input)
    for tok in lexer:
        token_records.append({
            "Token Type": tok.type,
            "Lexeme": str(tok.value),
            "Line": tok.lineno,
            "Char Pos": tok.lexpos
        })

    # 2. Syntax Analysis
    try:
        tree = parser.parse(code_input, lexer=lexer)
    except Exception as e:
        parse_error = str(e)

    # 3. Semantic Analysis
    if tree and not parse_error:
        try:
            analyzer.visit(tree)
        except Exception as e:
            semantic_error = str(e)

    with col2:
        st.subheader("Validation Status")
        if parse_error:
            st.error(f"Syntax Error: {parse_error}")
        elif semantic_error:
            st.error(f"{semantic_error}")
        else:
            st.success("All checks passed: Grammar verified & matrix dimensions match.")

# --- Inspection Tabs ---
tab_tokens, tab_ast, tab_symtab = st.tabs([
    "1. Lexer Tokens", 
    "2. Abstract Syntax Tree", 
    "3. Symbol Table"
])

with tab_tokens:
    if token_records:
        st.dataframe(pd.DataFrame(token_records), use_container_width=True)
    else:
        st.info("No tokens found.")

with tab_ast:
    if tree and not parse_error:
        st.graphviz_chart(generate_dot(tree))
        with st.expander("View Raw AST Hierarchy"):
            st.code(repr(tree), language="text")
    elif parse_error:
        st.warning("Cannot construct AST due to syntax errors.")

with tab_symtab:
    if analyzer.symtab.symbols:
        table_rows = []
        for name, info in analyzer.symtab.symbols.items():
            dim_display = f"{info['dimensions'][0]} x {info['dimensions'][1]}" if info['dimensions'] else "Scalar"
            table_rows.append({
                "Identifier": name,
                "Type": info["type"],
                "Dimensions": dim_display
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    else:
        st.info("Symbol table is empty or analysis failed.")
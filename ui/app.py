# ui/app.py
import streamlit as st
import pandas as pd
import html
from core.lexer import lexer, reset_lexer
from core.parser import parse_code
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
        if curr is None:
            return
        cid = f"node_{counter[0]}"
        counter[0] += 1

        if isinstance(curr, ast.Program):
            label = "Program"
        elif isinstance(curr, ast.Assignment):
            label = f"Assign: {curr.target.name}"
        elif isinstance(curr, ast.UnaryOp):
            label = f"UnaryOp: {curr.op}"
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
        elif isinstance(curr, ast.UnaryOp):
            walk(curr.operand, cid, "operand")
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

# --- VS Code-Style Diagnostic Snippet ---
def render_vscode_snippet(source_code, lineno, col, offending_text):
    lines = source_code.splitlines()
    if not lines:
        return ""
    
    target_idx = max(0, min(lineno - 1, len(lines) - 1))
    line_content = lines[target_idx]

    if offending_text and offending_text in line_content and offending_text != "EOF":
        parts = line_content.split(offending_text, 1)
        highlighted_line = (
            f"{html.escape(parts[0])}"
            f"<span style='border-bottom: 2px wavy #EF4444; color: #F87171; font-weight: bold; background: rgba(239, 68, 68, 0.15); padding: 0 3px;'>{html.escape(offending_text)}</span>"
            f"{html.escape(parts[1])}"
        )
    else:
        highlighted_line = f"<span style='border-bottom: 2px wavy #EF4444; color: #F87171;'>{html.escape(line_content)}</span>"

    return f"""
    <div style="background-color: #1E1E1E; color: #D4D4D4; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; border-radius: 6px; padding: 10px 14px; border: 1px solid #333333; margin: 8px 0 14px 0;">
        <div style="color: #6E7681; font-size: 11px; margin-bottom: 4px;">LOCATION: LINE {target_idx + 1}, COLUMN {col}</div>
        <div style="display: flex; gap: 12px; line-height: 1.5;">
            <span style="color: #6E7681; user-select: none;">{target_idx + 1:2d} |</span>
            <span>{highlighted_line}</span>
        </div>
    </div>
    """

# --- Layout ---
st.title("matrixForge - Phase 1 Visualizer")
st.caption("Pipeline: Lexical Analysis → Syntax Analysis (AST) → Semantic Analysis & Multi-Error Diagnostics")

default_code = """matrix A = [[1, 2, 3], [4, 5, 6]];
matrix B = [[1, 2], [3, 4], [5, 6]];
matrix C = -A * B;
matrix D = -C + [[10, 20], [30, 40]];
print(D);"""

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Source Input")
    uploaded_file = st.file_uploader("Upload a .mfg source file", type=["mfg", "txt"], help="Limit: 1 MB")
    
    if uploaded_file is not None:
        if uploaded_file.size > 1024 * 1024:
            st.error("File size exceeds 1 MB limit for matrixForge scripts.")
            code_input = default_code
        else:
            code_input = uploaded_file.read().decode("utf-8")
            st.text_area("File Contents:", code_input, height=200, disabled=True)
    else:
        code_input = st.text_area("Input matrixForge code:", default_code, height=200)

    compile_btn = st.button("Analyze Code", type="primary")

token_records = []
tree = None
all_errors = []
analyzer = SemanticAnalyzer()

if compile_btn or code_input:
    # 1. Lexical Analysis
    reset_lexer()
    lexer.input(code_input)
    for tok in lexer:
        token_records.append({
            "Token Type": tok.type,
            "Lexeme": str(tok.value),
            "Line": tok.lineno,
            "Char Pos": tok.lexpos
        })
    all_errors.extend(list(lexer.errors))

    # 2. Syntax Analysis with Error Recovery
    tree, parse_errors = parse_code(code_input, lexer)
    all_errors.extend(parse_errors)

    # 3. Semantic Analysis
    if tree is not None:
        analyzer.reset(source_code=code_input)
        analyzer.visit(tree)
        all_errors.extend(analyzer.errors)

    with col2:
        st.subheader("Validation Status")
        total_err_count = len(all_errors)

        if total_err_count > 0:
            st.error(f"❌ Compilation Failed: Found **{total_err_count} Error(s)** across pipeline.")

            for i, err in enumerate(all_errors, 1):
                err_badge = {
                    "Lexical Error": "🔴 Lexical Error",
                    "Syntax Error": "🟠 Syntax Error",
                    "Semantic Error": "🟣 Semantic Error"
                }.get(err.get("type"), "❌ Error")

                st.markdown(f"#### {i}. {err_badge} — `{err['message']}`")
                st.info(f"💡 **Suggested Fix:** {err['suggestion']}")
                
                # Dynamic fallback: resolve line number if missing or invalid
                line_no = err.get("line")
                col_no = err.get("col", 1)
                offending = err.get("offending", "")

                if not isinstance(line_no, int) or line_no < 1:
                    line_no = 1
                    if offending and offending in code_input:
                        for idx, l in enumerate(code_input.splitlines()):
                            if offending in l:
                                line_no = idx + 1
                                col_no = l.find(offending) + 1
                                break

                st.markdown(render_vscode_snippet(code_input, line_no, col_no, offending), unsafe_allow_html=True)
                st.divider()
        else:
            st.success("✅ All checks passed: Grammar verified, unary ops evaluated, & matrix dimensions match.")

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
    if tree:
        st.graphviz_chart(generate_dot(tree))
        with st.expander("View Raw AST Hierarchy"):
            st.code(repr(tree), language="text")
    else:
        st.warning("Cannot construct AST due to fatal syntax errors.")

with tab_symtab:
    if analyzer.symtab.symbols and len(all_errors) == 0:
        table_rows = []
        for name, info in analyzer.symtab.symbols.items():
            dim_display = f"{info['dimensions'][0]} x {info['dimensions'][1]}" if info['dimensions'] else "Scalar"
            table_rows.append({
                "Identifier": name,
                "Type": info["type"],
                "Dimensions": dim_display
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    elif analyzer.symtab.symbols and len(all_errors) > 0:
        st.warning("Symbol table contains partial entries due to compilation errors.")
        table_rows = []
        for name, info in analyzer.symtab.symbols.items():
            dim_display = f"{info['dimensions'][0]} x {info['dimensions'][1]}" if info['dimensions'] else "Unknown/Scalar"
            table_rows.append({
                "Identifier": name,
                "Type": info["type"],
                "Dimensions": dim_display
            })
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    else:
        st.info("Symbol table empty (resolve errors to inspect full table).")
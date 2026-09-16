# core/parser.py
import ply.yacc as yacc
from core.lexer import tokens, lexer
import core.ast_nodes as ast

# 1. Operator Precedence and Associativity
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS'),
)

# 2. Parsing Rules (Context-Free Grammar)

def p_program(p):
    '''program : statement_list'''
    line = p[1][0].lineno if p[1] else 1
    pos = p[1][0].lexpos if p[1] else 0
    p[0] = ast.Program(p[1], lineno=line, lexpos=pos)

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        stmts = p[1]
        if p[2] is not None:
            stmts.append(p[2])
        p[0] = stmts
    else:
        p[0] = [p[1]] if p[1] is not None else []

def p_statement_assign(p):
    '''statement : MATRIX_KW ID ASSIGN expression SEMI
                 | LET_KW ID ASSIGN expression SEMI'''
    target = ast.Identifier(p[2], lineno=p.lineno(2), lexpos=p.lexpos(2))
    p[0] = ast.Assignment(target, p[4], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_statement_print(p):
    '''statement : PRINT_KW LPAREN expression RPAREN SEMI'''
    p[0] = ast.PrintStmt(p[3], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_statement_error(p):
    '''statement : error SEMI'''
    p[0] = None

# 3. Expressions & Unary Operations

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    p[0] = ast.BinOp(p[1], p[2], p[3], lineno=p.lineno(2), lexpos=p.lexpos(2))

def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = ast.UnaryOp(p[1], p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_matrix(p):
    '''expression : LBRACKET row_list RBRACKET'''
    p[0] = ast.MatrixLiteral(p[2], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_row_list(p):
    '''row_list : row_list COMMA row
                | row'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_row(p):
    '''row : LBRACKET element_list RBRACKET'''
    p[0] = p[2]

def p_element_list(p):
    '''element_list : element_list COMMA expression
                    | expression'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_expression_term(p):
    '''expression : INT_LIT
                  | FLOAT_LIT'''
    p[0] = ast.Number(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))

def p_expression_id(p):
    '''expression : ID'''
    p[0] = ast.Identifier(p[1], lineno=p.lineno(1), lexpos=p.lexpos(1))

# 4. Diagnostic Utilities

def find_column(source_text, lexpos):
    if not source_text or lexpos < 0 or lexpos > len(source_text):
        return 1
    line_start = source_text.rfind('\n', 0, lexpos) + 1
    return (lexpos - line_start) + 1

def generate_syntax_suggestion(token):
    if not token:
        return "Check for missing closing delimiters ']', ')' or trailing semicolon ';'."
    if token.type == 'SEMI':
        return "Unexpected semicolon ';'. Check for missing closing bracket ']' or incomplete expression prior to ';'."
    elif token.type == 'LBRACKET':
        return "Unexpected '['. Ensure assignment operator '=' or separating comma ',' is not omitted."
    elif token.type in ('MATRIX_KW', 'LET_KW', 'PRINT_KW'):
        return "Missing semicolon ';' at the end of the preceding statement."
    elif token.type == 'ASSIGN':
        return "Unexpected '='. Verify valid identifier on the left-hand side of assignment."
    return f"Check statement syntax around '{token.value}'."

def p_error(p):
    source_text = getattr(parser, 'current_source', '')
    if p:
        col = find_column(source_text, p.lexpos)
        err = {
            "type": "Syntax Error",
            "message": f"Syntax error near '{p.value}' (Token: {p.type})",
            "line": p.lineno,
            "pos": p.lexpos,
            "col": col,
            "offending": str(p.value),
            "suggestion": generate_syntax_suggestion(p)
        }
    else:
        last_line = source_text.count('\n') + 1 if source_text else 1
        err = {
            "type": "Syntax Error",
            "message": "Unexpected end of input (incomplete statement or missing semicolon/bracket)",
            "line": last_line,
            "pos": len(source_text),
            "col": len(source_text.splitlines()[-1]) + 1 if source_text.splitlines() else 1,
            "offending": "EOF",
            "suggestion": "Check for unclosed delimiters ']', ')' or missing trailing semicolon ';'."
        }
    parser.errors.append(err)

parser = yacc.yacc()
parser.errors = []
parser.current_source = ""

def parse_code(code, lexer_instance=None):
    parser.errors = []
    parser.current_source = code
    target_lexer = lexer_instance if lexer_instance is not None else lexer
    target_lexer.lineno = 1
    tree = parser.parse(code, lexer=target_lexer, tracking=True)
    return tree, parser.errors
# core/parser.py
import ply.yacc as yacc

# Import the tokens list from our lexer so the parser knows what to expect
from core.lexer import tokens
import core.ast_nodes as ast

# 1. Parsing Rules (Context-Free Grammar)
# The 'p_' prefix tells PLY this is a syntax rule.
def p_program(p):
    '''program : statement_list'''
    p[0] = ast.Program(p[1])

def p_statement_list(p):
    '''statement_list : statement_list statement
                      | statement'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_statement_assign(p):
    '''statement : MATRIX_KW ID ASSIGN expression SEMI
                 | LET_KW ID ASSIGN expression SEMI'''
    p[0] = ast.Assignment(ast.Identifier(p[2]), p[4])

def p_statement_print(p):
    '''statement : PRINT_KW LPAREN expression RPAREN SEMI'''
    p[0] = ast.PrintStmt(p[3])

# 2. Expressions
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    p[0] = ast.BinOp(p[1], p[2], p[3])

def p_expression_group(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]

def p_expression_matrix(p):
    '''expression : LBRACKET row_list RBRACKET'''
    p[0] = ast.MatrixLiteral(p[2])

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
    p[0] = ast.Number(p[1])

def p_expression_id(p):
    '''expression : ID'''
    p[0] = ast.Identifier(p[1])

# 3. Error Handling
def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' (line {p.lineno})")
    else:
        print("Syntax error at EOF (End of File)")

# Build the parser
parser = yacc.yacc()

# --- Quick Test Block ---
if __name__ == '__main__':
    from core.lexer import lexer
    data = '''
    matrix A = [[1, 2], [3, 4]];
    print(A);
    '''
    # Run the parser on the data
    result = parser.parse(data, lexer=lexer)
    print("\n--- Abstract Syntax Tree ---")
    print(result)
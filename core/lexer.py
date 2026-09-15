import ply.lex as lex
tokens = (
    'ID', 'INT_LIT', 'FLOAT_LIT',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'ASSIGN',
    'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'COMMA', 'SEMI'
)
reserved = {
    'matrix': 'MATRIX_KW',
    'print': 'PRINT_KW',
    'let': 'LET_KW'
}
tokens = tokens + tuple(reserved.values())
t_PLUS     = r'\+'
t_MINUS    = r'-'
t_TIMES    = r'\*'
t_DIVIDE   = r'/'
t_ASSIGN   = r'='
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_LBRACE   = r'\{'
t_RBRACE   = r'\}'
t_COMMA    = r','
t_SEMI     = r';'
t_ignore = ' \t\r'
def t_FLOAT_LIT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t
def t_INT_LIT(t):
    r'\d+'
    t.value = int(t.value)
    return t
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'ID')
    return t
def t_newline(t):
    r'\r?\n+'
    t.lexer.lineno += len(t.value)
def t_error(t):
    print(f"Lexical Error: Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)
lexer = lex.lex()

# --- Quick Test Block ---
if __name__ == '__main__':
    data = '''
    matrix A = [[1, 2.5], [3, 4]];
    print(A);
    '''
    lexer.input(data)
    for tok in lexer:
        print(tok)
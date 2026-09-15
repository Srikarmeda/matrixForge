import ply.lex as lex

# 1. List of token names. This is always required by PLY.
tokens = (
    'ID', 'INT_LIT', 'FLOAT_LIT',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'ASSIGN',
    'LBRACKET', 'RBRACKET', 'LPAREN', 'RPAREN', 'LBRACE', 'RBRACE',
    'COMMA', 'SEMI'
)

# 2. Reserved keywords map (we check these after finding an ID)
reserved = {
    'matrix': 'MATRIX_KW',
    'print': 'PRINT_KW',
    'let': 'LET_KW'
}
tokens = tokens + tuple(reserved.values())

# 3. Simple regex rules for basic operators
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

# 4. Ignored characters (spaces, tabs, and Windows CR)
t_ignore = ' \t\r'

# 5. Complex regex rules (Functions)
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
    # Check if the ID is actually a reserved keyword
    t.type = reserved.get(t.value, 'ID')
    return t

# Track line numbers for error reporting
def t_newline(t):
    r'\r?\n+'
    t.lexer.lineno += len(t.value)

# Error handling rule
def t_error(t):
    print(f"Lexical Error: Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

# Build the lexer
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
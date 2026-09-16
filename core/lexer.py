# core/lexer.py
import ply.lex as lex

# Reserved keywords mapping
reserved = {
    'matrix': 'MATRIX_KW',
    'let': 'LET_KW',
    'print': 'PRINT_KW',
}

# Token list definition
tokens = [
    # Literals & Identifiers
    'ID',
    'INT_LIT',
    'FLOAT_LIT',

    # Operators
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'ASSIGN',

    # Delimiters
    'LPAREN',
    'RPAREN',
    'LBRACKET',
    'RBRACKET',
    'COMMA',
    'SEMI',
] + list(reserved.values())

# Simple token regular expression rules
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_ASSIGN = r'='
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COMMA = r','
t_SEMI = r';'

# Ignored characters: spaces, tabs, and carriage returns
t_ignore = ' \t\r'

# Comment handling: ignore single-line comments starting with '//'
def t_COMMENT(t):
    r'//.*'
    pass

# Float literal rule (must precede int rule)
def t_FLOAT_LIT(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

# Integer literal rule
def t_INT_LIT(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Identifier and reserved keyword matching
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

# Newline tracking for precise line numbering
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Lexical error collection: collects error details without aborting tokenization
def t_error(t):
    col = find_column(t.lexer.lexdata, t)
    error_record = {
        "type": "Lexical Error",
        "message": f"Illegal character '{t.value[0]}'",
        "line": t.lineno,
        "pos": t.lexpos,
        "col": col,
        "offending": t.value[0],
        "suggestion": f"Remove unexpected character '{t.value[0]}' or replace with a valid identifier/operator."
    }
    t.lexer.errors.append(error_record)
    t.lexer.skip(1)

# Helper function to calculate column number from absolute lexpos
def find_column(input_text, token):
    line_start = input_text.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

# Build the lexer
lexer = lex.lex()
lexer.errors = []

def reset_lexer():
    """Resets the lexer state and clears collected errors."""
    lexer.lineno = 1
    lexer.errors = []

# Quick test routine
if __name__ == '__main__':
    reset_lexer()
    sample_code = """
    matrix A = [[1, 2], [3, 4]];
    $ // invalid character test
    matrix B = -A + [[5, 6], [7, 8]];
    # // another invalid character
    print(B);
    """
    lexer.input(sample_code)
    print("--- TOKENS ---")
    for tok in lexer:
        print(tok)
    print("\n--- COLLECTED LEXICAL ERRORS ---")
    for err in lexer.errors:
        print(err)
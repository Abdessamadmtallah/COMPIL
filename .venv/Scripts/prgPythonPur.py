from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import re

# ------------------------------
# 1. Code source MiniPython
# ------------------------------
code_source = """
int x, y;
x = 5;
y = x + 2;
print(y);
"""

# ------------------------------
# 2. Analyse lexicale
# ------------------------------
token_specification = [
    ('NUMBER', r'\d+'), ('INT', r'int'), ('PRINT', r'print'),
    ('ID', r'[A-Za-z_]\w*'), ('COMMA', r','), ('SEMICOLON', r';'),
    ('PLUS', r'\+'), ('EQUAL', r'='), ('LPAR', r'\('), ('RPAR', r'\)'),
    ('SKIP', r'[ \t\n]+')
]
regex = '|'.join(f'(?P<{n}>{p})' for n, p in token_specification)
tokens = [(m.lastgroup, m.group()) for m in re.finditer(regex, code_source) if m.lastgroup != 'SKIP']

print("\n=== Phase lexicale ===")
for t in tokens:
    print(t)

# ------------------------------
# 3. Analyse syntaxique & construction AST
# ------------------------------
symbol_table = {}
ast = []

i = 0
while i < len(tokens):
    tok, val = tokens[i]
    if tok == 'INT':  # Déclaration de variables
        i += 1
        vars_list = []
        while tokens[i][0] != 'SEMICOLON':
            if tokens[i][0] == 'ID':
                vars_list.append(tokens[i][1])
            i += 1
        # L-attribué : type hérité du parent
        for v in vars_list:
            symbol_table[v] = 'int'
        ast.append(('Decl (L-attribué)', [('Var: ' + v + ' (type=int)') for v in vars_list]))
        i += 1
    elif tok == 'ID':  # Assignation
        var_name = val
        i += 2  # skip '='
        left_tok, left_val = tokens[i]
        i += 1
        if i < len(tokens) and tokens[i][0] == 'PLUS':
            i += 1
            right_val = int(tokens[i][1])
            i += 1
            expr = ('Expr: +', [('Var: ' + left_val), ('Const: ' + str(right_val))])
        else:
            expr = ('Expr', [('Const: ' + left_val) if left_val.isdigit() else ('Var: ' + left_val)])
        ast.append(('Assign (S-attribué)', [('Var: ' + var_name), expr]))
    elif tok == 'PRINT':
        i += 2  # skip '('
        var_name = tokens[i][1]
        i += 2  # skip ')' and ';'
        ast.append(('Print (S-attribué)', [('Var: ' + var_name)]))

print("\n=== AST syntaxique brut ===")
for node in ast:
    print(node)

# ------------------------------
# 4. Analyse sémantique simple
# ------------------------------
def semantic_check(ast, symbol_table):
    new_ast = []
    for stmt in ast:
        if stmt[0].startswith('Decl'):
            new_ast.append(stmt)
        elif stmt[0].startswith('Assign'):
            var = stmt[1][0].split(': ')[1]
            if var not in symbol_table:
                raise Exception(f"Erreur sémantique : variable {var} non déclarée")
            new_ast.append(stmt)
        elif stmt[0].startswith('Print'):
            var = stmt[1][0].split(': ')[1]
            if var not in symbol_table:
                raise Exception(f"Erreur sémantique : variable {var} non déclarée")
            new_ast.append(stmt)
    return new_ast

ast_semantic = semantic_check(ast, symbol_table)
print("\n=== AST après analyse sémantique ===")
for node in ast_semantic:
    print(node)

# ------------------------------
# 5. Visualisation AST avec anytree
# ------------------------------
def build_anytree(node, parent=None):
    if isinstance(node, tuple):
        n = Node(node[0], parent=parent)
        for c in node[1]:
            build_anytree(c, n)
        return n
    elif isinstance(node, list):
        n = Node("list", parent=parent)
        for item in node:
            build_anytree(item, n)
        return n
    else:
        Node(str(node), parent=parent)
        return parent

root_node = build_anytree(("Program", ast_semantic))
print("\n=== AST visuel console ===")
for pre, fill, node in RenderTree(root_node):
    print(f"{pre}{node.name}")

DotExporter(root_node).to_picture("ast_graphviz.png")
print("\n✅ AST exporté en image : ast_graphviz.png")

# ------------------------------
# 6. Exécution MiniPython
# ------------------------------
def execute(ast, symbol_table):
    runtime = {var: None for var in symbol_table.keys()}
    for stmt in ast:
        if stmt[0].startswith('Assign'):
            var = stmt[1][0].split(': ')[1]
            val = stmt[2]
            if isinstance(val, tuple) and val[0] == 'Expr: +':
                left = runtime[val[1][0].split(': ')[1]]
                right = int(val[2][0].split(': ')[1]) if 'Const' in val[2][0] else runtime[val[2][0].split(': ')[1]]
                runtime[var] = left + right
            else:
                runtime[var] = int(val[0].split(': ')[1]) if 'Const' in val[0] else runtime[val[0].split(': ')[1]]
        elif stmt[0].startswith('Print'):
            var = stmt[1][0].split(': ')[1]
            print(runtime[var])

print("\n=== Exécution MiniPython ===")
execute(ast_semantic, symbol_table)

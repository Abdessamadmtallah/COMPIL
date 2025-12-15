from lark import Lark, Transformer
from anytree import Node, RenderTree
from anytree.exporter import DotExporter

# Charger la grammaire
with open("minipython.lark", "r") as f:
    grammar = f.read()

parser = Lark(grammar, start="start", parser="lalr", lexer="basic")

code_source = """
int x, y;
x = 5;
y = x + 2;
print(y);
"""
 
print("\n=== Phase lexicale (Lark) ===")
tokens = list(parser.lex(code_source))
for t in tokens:
    print(t)


# Transformer qui convertit l'arbre Lark en tuples python simples
class SyntaxTransformer(Transformer):
    def decl(self, items):
        vars = []
        for item in items:
            if isinstance(item, list):
                vars.extend(item)
            elif hasattr(item, 'data') and item.data == 'var_list':
                vars.extend([str(child) for child in item.children if str(child) != ","])
            else:
                if str(item) != ",":
                    vars.append(str(item))
        return ("decl(L)", vars, 'int')

    def var_list(self, items):
        return [str(i) for i in items if str(i) != ","]

    def assign(self, items):
        return ("assign(S)", str(items[0]), items[1])

    def add(self, items):
        return ('+(S)', str(items[0]), int(items[1]))

    def print_stmt(self, items):
        return ("print(S)", str(items[0]))

    def NUMBER(self, n):
        return int(n)

    def CNAME(self, n):
        return str(n)

    def start(self, items):
        return items


tree = parser.parse(code_source)
ast_syntax = SyntaxTransformer().transform(tree)

print("\n=== AST syntaxique (Lark) ===")
for node in ast_syntax:
    print(node)


# Analyse sémantique
class SemanticTransformer:
    def __init__(self):
        self.symbol_table = {}

    def check(self, ast_list):
        new_ast = []
        for stmt in ast_list:
            if stmt[0] == "decl(L)":
                for var in stmt[1]:
                    if var in self.symbol_table:
                        raise Exception(f"Erreur : variable {var} déjà déclarée")
                    self.symbol_table[var] = 'int'
                new_ast.append(stmt)

            elif stmt[0] == "assign(S)":
                var, expr = stmt[1], stmt[2]
                if var not in self.symbol_table:
                    raise Exception(f"Erreur : variable {var} non déclarée")
                new_ast.append(stmt)

            elif stmt[0] == "print(S)":
                var = stmt[1]
                if var not in self.symbol_table:
                    raise Exception(f"Erreur : variable {var} non déclarée")
                new_ast.append(stmt)

            elif stmt[0] == "+(S)":
                left, right = stmt[1], stmt[2]
                if isinstance(left, str) and left not in self.symbol_table:
                    raise Exception(f"Erreur : variable {left} non déclarée")
                new_ast.append(stmt)
        return new_ast


semantic = SemanticTransformer()
ast_semantic = semantic.check(ast_syntax)

print("\n=== AST après analyse sémantique ===")
for node in ast_semantic:
    print(node)


def build_anytree(node, parent=None):
    if isinstance(node, tuple):
        n = Node(node[0], parent=parent)
        for c in node[1:]:
            build_anytree(c, n)
        return n
    elif isinstance(node, list):
        n = Node("list", parent=parent)
        for item in node:
            build_anytree(item, n)
        return n
    else:
        return Node(str(node), parent=parent)


root = build_anytree(("root", *ast_semantic))

print("\n=== AST visuel console ===")
for pre, fill, node in RenderTree(root):
    print(f"{pre}{node.name}")

DotExporter
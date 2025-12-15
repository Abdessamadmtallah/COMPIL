from lark import Lark, Transformer
from anytree import Node, RenderTree
from anytree.exporter import DotExporter
import os
import sys

# Grammaire MiniPython intégrée
# Grammaire MiniPython intégrée
grammar = r"""
start: (decl | stmt)*

decl: "int" NAME ("," NAME)* ";"

stmt: assign | print_stmt

assign: NAME "=" expr ";"

print_stmt: "print" NAME ";"

expr: NAME | NUMBER

NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+/

%ignore /\s+/
"""

try:
    parser = Lark(grammar, parser="earley", maybe_create_child_filter=False)
except Exception as e:
    print(f"✗ Erreur création du parseur: {e}")
    sys.exit(1)


# ---------------------------------------------------
# AST syntaxique avec Lark Transformer
# ---------------------------------------------------
class SyntaxTransformer(Transformer):
    def start(self, items):
        return [item for item in items if item]

    def decl(self, items):
        vars_list = [str(item) for item in items]
        return ("decl", vars_list)

    def assign(self, items):
        return ("assign", str(items[0]), items[1])

    def print_stmt(self, items):
        return ("print", str(items[0]))

    def expr(self, items):
        return items[0]

    def NAME(self, token):
        return str(token)

    def NUMBER(self, token):
        return int(token)


# ---------------------------------------------------
# Analyse sémantique
# ---------------------------------------------------
class SemanticTransformer:
    def __init__(self):
        self.symbol_table = {}

    def check(self, ast_list):
        new_ast = []
        for stmt in ast_list:
            if stmt[0] == "decl":
                var_list = stmt[1]
                for var in var_list:
                    if var in self.symbol_table:
                        raise Exception(f"Erreur : variable {var} déjà déclarée")
                    self.symbol_table[var] = 'int'
                new_ast.append(stmt)

            elif stmt[0] == "assign":
                var, expr = stmt[1], stmt[2]
                if var not in self.symbol_table:
                    raise Exception(f"Erreur : variable {var} non déclarée")
                new_ast.append(stmt)

            elif stmt[0] == "print":
                var = stmt[1]
                if var not in self.symbol_table and not var.isdigit():
                    raise Exception(f"Erreur : variable {var} non déclarée")
                new_ast.append(stmt)

        return new_ast


# ---------------------------------------------------
# Visualisation AST
# ---------------------------------------------------
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
        Node(str(node), parent=parent)
        return parent


# ---------------------------------------------------
# Exécution MiniPython
# ---------------------------------------------------
def execute(ast, symbol_table):
    runtime = {var: 0 for var in symbol_table.keys()}

    def eval_expr(expr):
        if isinstance(expr, int):
            return expr
        elif isinstance(expr, str):
            if expr in runtime:
                return runtime[expr]
            try:
                return int(expr)
            except:
                return 0
        elif isinstance(expr, tuple):
            op = expr[0]
            if len(expr) >= 3:
                left = eval_expr(expr[1])
                right = eval_expr(expr[2])
                if op == '+':
                    return left + right
                elif op == '-':
                    return left - right
                elif op == '*':
                    return left * right
                elif op == '/':
                    return left / right if right != 0 else 0
        return expr

    for stmt in ast:
        if stmt[0] == 'assign':
            var = stmt[1]
            val = eval_expr(stmt[2])
            if var in runtime:
                runtime[var] = val

        elif stmt[0] == 'print':
            var = stmt[1]
            result = eval_expr(var)
            print(result)


# ---------------------------------------------------
# Fonction de compilation complète
# ---------------------------------------------------
def compile_and_execute(code_source, show_details=True):
    print("\n" + "=" * 70)
    print("COMPILATION ET EXÉCUTION MINIPYTHON")
    print("=" * 70)

    # Analyse lexicale
    print("\n### Phase 1: Analyse Lexicale ###")
    try:
        tokens = list(parser.lex(code_source))
        print(f"✓ {len(tokens)} tokens trouvés")
        if show_details and len(tokens) <= 20:
            for t in tokens:
                print(f"  {t}")
    except Exception as e:
        print(f"✗ Erreur lexicale: {e}")
        return False

    # Parsing et AST syntaxique
    print("\n### Phase 2: Parsing + AST Syntaxique ###")
    try:
        tree = parser.parse(code_source)
        ast_syntax = SyntaxTransformer().transform(tree)
        print("✓ Parsing réussi")
        print("AST syntaxique:")
        for node in ast_syntax:
            print(f"  {node}")
    except Exception as e:
        print(f"✗ Erreur de parsing: {e}")
        return False

    # Analyse sémantique
    print("\n### Phase 3: Analyse Sémantique ###")
    try:
        semantic = SemanticTransformer()
        ast_semantic = semantic.check(ast_syntax)
        print("✓ Analyse sémantique réussie")
        print("Table des symboles:")
        for var, typ in semantic.symbol_table.items():
            print(f"  {var}: {typ}")
    except Exception as e:
        print(f"✗ Erreur sémantique: {e}")
        return False

    # Visualisation AST
    print("\n### Phase 4: Visualisation AST ###")
    try:
        root = build_anytree(("root", *ast_semantic))
        print("AST visuel:")
        for pre, fill, node in RenderTree(root):
            print(f"{pre}{node.name}")

        # Optionnel: sauvegarder l'image
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(script_dir, "ast_lark.png")
            DotExporter(root).to_picture(output_path)
            print(f"✓ Image AST sauvegardée : {output_path}")
        except:
            pass
    except Exception as e:
        print(f"⚠ Erreur visualisation: {e}")

    # Exécution
    print("\n### Phase 5: Exécution ###")
    print("Résultat:")
    try:
        execute(ast_semantic, semantic.symbol_table)
        print("\n✓ Exécution réussie")
        return True
    except Exception as e:
        print(f"✗ Erreur d'exécution: {e}")
        return False


# ---------------------------------------------------
# Mode interactif
# ---------------------------------------------------
def main():
    print("\n" + "╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "COMPILATEUR MINIPYTHON INTERACTIF" + " " * 20 + "║")
    print("╚" + "=" * 68 + "╝")

    while True:
        print("\n" + "-" * 70)
        print("OPTIONS:")
        print("  1. Saisir le code directement")
        print("  2. Charger depuis un fichier")
        print("  3. Exemple de code")
        print("  4. Quitter")
        print("-" * 70)

        choice = input("\nChoisissez une option (1/2/3/4): ").strip()

        if choice == "1":
            print("\n" + "─" * 70)
            print("Saisissez votre code MiniPython")
            print("(Terminez par une ligne vide)")
            print("─" * 70)

            lines = []
            while True:
                try:
                    line = input()
                    if not line.strip():
                        break
                    lines.append(line)
                except EOFError:
                    break

            code = "\n".join(lines)
            if code.strip():
                compile_and_execute(code)
            else:
                print("⚠ Code vide!")

        elif choice == "2":
            filename = input("\nEntrez le chemin du fichier: ").strip()
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    code = f.read()
                print(f"✓ Fichier '{filename}' chargé")
                compile_and_execute(code)
            except FileNotFoundError:
                print(f"✗ Erreur: Fichier '{filename}' non trouvé")
            except Exception as e:
                print(f"✗ Erreur: {e}")

        elif choice == "3":
            code = """int x, y;
x = 5;
y = x + 2;
print(y);"""
            print(f"Exemple:\n{code}\n")
            compile_and_execute(code)

        elif choice == "4":
            print("\n✓ Au revoir!")
            break

        else:
            print("⚠ Option invalide!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Mode ligne de commande avec fichier
        filename = sys.argv[1]
        try:
            with open(filename, "r", encoding="utf-8") as f:
                code = f.read()
            print(f"Chargement du fichier: {filename}")
            compile_and_execute(code)
        except FileNotFoundError:
            print(f"✗ Erreur: Fichier '{filename}' non trouvé")
            sys.exit(1)
    else:
        # Mode interactif
        main()
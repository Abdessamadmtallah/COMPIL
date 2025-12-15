from lark import Lark, Transformer, Tree
from anytree import Node, RenderTree
from anytree.exporter import DotExporter


# ============================================================
# PROGRAMME AVEC LARK - Version Automatisée
# ============================================================

class MiniPythonLarkAnalyzer:
    def __init__(self, grammar_file="minipython.lark1"):
        try:
            with open(grammar_file, "r") as f:
                grammar = f.read()
        except FileNotFoundError:
            print(f"⚠️  Fichier {grammar_file} non trouvé. Grammaire intégrée utilisée.")
            grammar = self.get_default_grammar()

        self.parser = Lark(grammar, start="start", parser="lalr", lexer="basic")
        self.symbol_table = {}
        self.tac_code = []

    @staticmethod
    def get_default_grammar():
        return '''
        start: statement*

        statement: decl
                 | assign
                 | while_stmt
                 | if_stmt
                 | print_stmt

        decl: "int" var_list ";"
        var_list: CNAME ("," CNAME)*

        assign: CNAME "=" expr ";"

        ?expr: term
             | expr "+" term -> add
             | expr "-" term -> sub

        ?term: factor
             | term "*" factor -> mul
             | term "/" factor -> div

        ?factor: NUMBER
               | CNAME
               | "(" expr ")"

        while_stmt: "while" "(" condition ")" "{" statement* "}"
        if_stmt: "if" "(" condition ")" "{" statement* "}" ("else" "{" statement* "}")?

        ?condition: expr comparison_op expr -> compare

        comparison_op: "==" -> eq
                     | "!=" -> ne
                     | "<" -> lt
                     | ">" -> gt

        print_stmt: "print" "(" CNAME ")" ";"

        %import common.CNAME
        %import common.NUMBER
        %import common.WS
        %ignore WS
        '''

    def tokenize(self, code_source):
        """Analyse lexicale avec Lark"""
        return list(self.parser.lex(code_source))

    def parse(self, code_source):
        """Analyse syntaxique avec Lark"""
        return self.parser.parse(code_source)

    class SyntaxTransformer(Transformer):
        """Transformateur pour générer l'AST"""

        def decl(self, items):
            return ("decl(L-attribué)", items, "int")

        def assign(self, items):
            return ("assign(S-attribué)", items[0], items[1])

        def add(self, items):
            return ("+", items[0], items[1])

        def sub(self, items):
            return ("-", items[0], items[1])

        def mul(self, items):
            return ("*", items[0], items[1])

        def div(self, items):
            return ("/", items[0], items[1])

        def while_stmt(self, items):
            return ("while(S-attribué)", items[0], items[1:])

        def if_stmt(self, items):
            return ("if(S-attribué)", items[0], items[1:])

        def print_stmt(self, items):
            return ("print(S-attribué)", str(items[0]))

        def compare(self, items):
            return ("compare", items[0], items[1])

        def eq(self, items):
            return "=="

        def ne(self, items):
            return "!="

        def lt(self, items):
            return "<"

        def gt(self, items):
            return ">"

        def var_list(self, items):
            return items

        def CNAME(self, token):
            return str(token)

        def NUMBER(self, token):
            return int(token)

    def analyze(self, code_source):
        """Analyse complète"""
        try:
            # 1. Lexicale
            print("\n--- Phase Lexicale (Lark) ---")
            tokens = self.tokenize(code_source)
            for tok in tokens:
                print(f"  {tok}")

            # 2. Syntaxique
            print("\n--- Analyse Syntaxique (Lark) ---")
            tree = self.parse(code_source)
            ast = self.SyntaxTransformer().transform(tree)
            print(f"  AST généré: {ast}")

            # 3. Sémantique
            print("\n--- Analyse Sémantique ---")
            self.semantic_check(ast)
            print(f"  Symboles déclarés: {self.symbol_table}")

            # 4. TAC
            print("\n--- Code Intermédiaire (TAC) ---")
            self.generate_tac(ast)
            for i, instr in enumerate(self.tac_code, 1):
                print(f"  {i}: {instr}")

            # 5. Visualisation
            print("\n--- Visualisation AST ---")
            self.visualize_ast(ast)

            return ast

        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None

    def semantic_check(self, ast):
        """Vérification sémantique"""
        if isinstance(ast, tuple):
            if ast[0] == "decl(L-attribué)":
                for var in ast[1]:
                    if var in self.symbol_table:
                        raise Exception(f"Variable {var} déjà déclarée")
                    self.symbol_table[var] = "int"

            elif ast[0] == "assign(S-attribué)":
                var_name = str(ast[1])
                if var_name not in self.symbol_table:
                    raise Exception(f"Variable {var_name} non déclarée")

            elif ast[0] == "print(S-attribué)":
                var_name = str(ast[1])
                if var_name not in self.symbol_table:
                    raise Exception(f"Variable {var_name} non déclarée")

    def generate_tac(self, ast):
        """Génération du TAC"""
        self.tac_code = []

        if isinstance(ast, tuple):
            if ast[0] == "decl(L-attribué)":
                for var in ast[1]:
                    self.tac_code.append(f"DECLARE {var}")

            elif ast[0] == "assign(S-attribué)":
                var_name = str(ast[1])
                expr = ast[2]

                if isinstance(expr, int):
                    self.tac_code.append(f"LOAD {var_name}, {expr}")
                elif isinstance(expr, str):
                    self.tac_code.append(f"LOAD {var_name}, {expr}")
                elif isinstance(expr, tuple):
                    self.tac_code.append(f"# Opération: {expr}")

            elif ast[0] == "print(S-attribué)":
                var_name = str(ast[1])
                self.tac_code.append(f"PRINT {var_name}")

    def visualize_ast(self, ast, filename="ast_lark.png"):
        """Visualisation de l'AST"""

        def build_anytree(node, parent=None):
            if isinstance(node, tuple):
                n = Node(str(node[0]), parent=parent)
                for item in node[1:]:
                    build_anytree(item, n)
                return n
            elif isinstance(node, list):
                n = Node("list", parent=parent)
                for item in node:
                    build_anytree(item, n)
                return n
            else:
                Node(str(node), parent=parent)
                return parent

        root = build_anytree(("root", ast))

        for pre, fill, node in RenderTree(root):
            print(f"{pre}{node.name}")

        try:
            DotExporter(root).to_picture(filename)
            print(f"✓ AST exporté: {filename}")
        except Exception as e:
            print(f"Erreur export: {e}")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

def main():
    print("=" * 60)
    print("MiniPython - Analyse avec Lark")
    print("=" * 60)

    analyzer = MiniPythonLarkAnalyzer()

    # Code de test ou saisie utilisateur
    choice = input("\n1. Utiliser le code par défaut\n2. Saisir du code\nChoix: ").strip()

    if choice == "1":
        code_source = """
int x, y;
x = 5;
y = x + 2;
print(y);
"""
    else:
        print("\n--- Entrez votre code (tapez 'FIN' seul pour terminer) ---")
        lines = []
        while True:
            line = input()
            if line.strip() == "FIN":
                break
            lines.append(line)
        code_source = "\n".join(lines)

    print(f"\n--- Code Source ---\n{code_source}")
    analyzer.analyze(code_source)


if __name__ == "__main__":
    main()
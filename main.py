from analizador_lexico import AnalizadorLexico
from analizador_sintactico import AnalizadorSintactico
from analizador_semantico import AnalizadorSemantico
from generador_codigo import GeneradorCodigo

codigo_original = """
inicio
a = 10;
b = 20;
c = a + b * 2;
si (c > 30) entonces
    escribir(c);
    d = c - 10;
finsi
escribir(d);
fin
"""

codigo_nuevo = """
int x = 10;
void test(int a) {
    int y = a * 2;
    {
        float x = 5.5;
        y = y + x;
    }
    x = y + 1;
    escribir(z);
}
"""


def ejecutar(titulo: str, codigo: str):
    separador = "═" * 60
    print(f"\n{separador}")
    print(f"  {titulo}")
    print(separador)

    print("\n--- 1. LÉXICO ---")
    lexer = AnalizadorLexico(codigo)
    tokens = lexer.tokenizar()
    print("TOKENS:", tokens)

    print("\n--- 2. SINTÁCTICO ---")
    parser = AnalizadorSintactico(tokens)
    ast = parser.analizar()
    print("AST construido con éxito.")

    print("\n--- 3. SEMÁNTICO ---")
    semantico = AnalizadorSemantico()
    semantico.visitar(ast)
    print("TABLA DE SÍMBOLOS (global):", semantico.tabla_simbolos)
    semantico.imprimir_resumen_final()

    print("--- 4. CÓDIGO DE TRES DIRECCIONES ---")
    generador = GeneradorCodigo()
    generador.generar(ast)
    generador.imprimir()


if __name__ == "__main__":
    ejecutar("EJEMPLO 1 — Lenguaje original (INICIO/FIN)", codigo_original)
    ejecutar("EJEMPLO 2 — Pseudo-C++ con tipos y bloques", codigo_nuevo)
class TablaSimbolos:
    """Tabla de símbolos con soporte para ámbitos anidados."""

    def __init__(self, nombre: str, padre=None):
        self.nombre = nombre
        self.padre = padre
        self.simbolos: dict = {}   
        self.historial: list = []  
    def declarar(self, nombre: str, tipo: str, valor=None):
        if nombre in self.simbolos:
            raise Exception(
                f"Error semántico: '{nombre}' ya fue declarado en el ámbito '{self.nombre}'."
            )
        self.simbolos[nombre] = {"tipo": tipo, "valor": valor}
        self.historial.append(
            f"  [DECLARAR] {nombre}: {tipo} = {valor}  (ámbito: {self.nombre})"
        )

    def obtener(self, nombre: str) -> dict:
        """Busca desde el ámbito actual hacia el padre (resolución léxica)."""
        if nombre in self.simbolos:
            return self.simbolos[nombre]
        if self.padre:
            return self.padre.obtener(nombre)
        raise Exception(f"Error semántico: Variable no definida → '{nombre}'")

    def obtener_tipo_variable(self, nombre: str) -> str:
        """Devuelve el tipo de la variable más cercana (shadowing incluido)."""
        return self.obtener(nombre)["tipo"]

    def asignar(self, nombre: str, valor):
        """Asigna valor a la variable más cercana visible."""
        if nombre in self.simbolos:
            self.simbolos[nombre]["valor"] = valor
            self.historial.append(
                f"  [ASIGNAR]  {nombre} = {valor}  (ámbito: {self.nombre})"
            )
            return
        if self.padre:
            self.padre.asignar(nombre, valor)
        else:
            raise Exception(f"Error semántico: Variable no definida → '{nombre}'")


    def abrir_ambito(self, nombre: str) -> "TablaSimbolos":
        hijo = TablaSimbolos(nombre, padre=self)
        self.historial.append(f"\n  [ABRIR]  ── ámbito '{nombre}' ──")
        return hijo

    def cerrar_ambito(self) -> "TablaSimbolos":
        if self.padre is None:
            raise Exception("No se puede cerrar el ámbito global.")
        self.padre.historial.append(
            f"  [CERRAR] ── ámbito '{self.nombre}' cerrado ──\n"
        )
        return self.padre


    def imprimir(self, indent: int = 0):
        prefijo = "  " * indent
        print(f"{prefijo}┌─ Ámbito: '{self.nombre}'")
        for nombre, info in self.simbolos.items():
            print(f"{prefijo}│  {nombre}: {info['tipo']} = {info['valor']}")
        print(f"{prefijo}└{'─' * 30}")
from nodes import (
    Programa, Asignacion, Imprimir, Si,
    OperacionBinaria, Numero, Variable,
    Bloque, Declaracion, Funcion,
)


class GeneradorCodigo:
    def __init__(self):
        self.contador_temporales = 0
        self.instrucciones: list[str] = []   
        self._pila_ambitos: list[dict] = [{}]


    def nuevo_temporal(self) -> str:
        self.contador_temporales += 1
        return f"t{self.contador_temporales}"


    def _nombre_actual(self, nombre: str) -> str:
        """Devuelve el nombre renombrado más cercano en la pila de ámbitos."""
        for ambito in reversed(self._pila_ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return nombre  

    def _registrar_variable(self, nombre: str, sufijo: str = "") -> str:
        """
        Registra una variable en el ámbito actual.
        Si ya existe en un ámbito padre, aplica sufijo (_local, _1, …).
        """
        existe_arriba = any(
            nombre in ambito
            for ambito in self._pila_ambitos[:-1]
        )
        nombre_final = f"{nombre}{sufijo}" if existe_arriba and sufijo else nombre
        if existe_arriba and not sufijo:
            nombre_final = f"{nombre}_L{len(self._pila_ambitos)}"
        self._pila_ambitos[-1][nombre] = nombre_final
        return nombre_final


    def _emitir(self, instruccion: str):
        self.instrucciones.append(instruccion)


    def generar(self, nodo):
        metodo = getattr(self, f"gen_{type(nodo).__name__}")
        return metodo(nodo)


    def gen_Programa(self, nodo):
        for sentencia in nodo.sentencias:
            self.generar(sentencia)

    def gen_Asignacion(self, nodo):
        valor = self.generar(nodo.valor)
        nombre = self._nombre_actual(nodo.nombre)
        self._emitir(f"{nombre} = {valor}")

    def gen_Imprimir(self, nodo):
        valor = self.generar(nodo.valor)
        self._emitir(f"escribir {valor}")

    def gen_Si(self, nodo):
        condicion = self.generar(nodo.condicion)
        etiqueta = f"L{self.contador_temporales + 1}"
        self._emitir(f"if_false {condicion} goto {etiqueta}")
        for sentencia in nodo.cuerpo:
            self.generar(sentencia)
        self._emitir(f"{etiqueta}:")

    def gen_OperacionBinaria(self, nodo):
        izq = self.generar(nodo.izquierda)
        der = self.generar(nodo.derecha)
        temp = self.nuevo_temporal()
        self._emitir(f"{temp} = {izq} {nodo.operador} {der}")
        return temp

    def gen_Numero(self, nodo):
        return str(nodo.valor)

    def gen_Variable(self, nodo):
        return self._nombre_actual(nodo.nombre)


    def gen_Declaracion(self, nodo):
        """int/float nombre = expr;  →  nombre_renombrado = valor"""
        sufijo = "_local" if len(self._pila_ambitos) > 1 else ""
        nombre_final = self._registrar_variable(nodo.nombre, sufijo)
        if nodo.valor:
            valor = self.generar(nodo.valor)
            self._emitir(f"{nombre_final} = {valor}")
        else:
            self._emitir(f"{nombre_final} = _sin_inicializar_")
        return nombre_final

    def gen_Bloque(self, nodo):
        """{ sentencias }  →  abre y cierra un nivel de pila"""
        self._pila_ambitos.append({})
        self._emitir("# ── inicio bloque ──")
        for sentencia in nodo.sentencias:
            self.generar(sentencia)
        self._emitir("# ── fin bloque ──")
        self._pila_ambitos.pop()

    def gen_Funcion(self, nodo):
        """void/int nombre(params) { cuerpo }"""
        self._emitir(f"\n# función {nodo.nombre}({', '.join(n for _, n in nodo.parametros)}):")
        self._pila_ambitos.append({})
        for tipo_p, nombre_p in nodo.parametros:
            self._pila_ambitos[-1][nombre_p] = nombre_p
            self._emitir(f"param {nombre_p}: {tipo_p}")
        for sentencia in nodo.cuerpo.sentencias:
            self.generar(sentencia)
        self._pila_ambitos.pop()
        self._emitir(f"# fin función {nodo.nombre}\n")


    def imprimir(self):
        print("─" * 50)
        print("  CÓDIGO DE TRES DIRECCIONES (C3D)")
        print("─" * 50)
        for i, instr in enumerate(self.instrucciones, 1):
            if instr.startswith("#"):
                print(f"      {instr}")
            else:
                print(f"  {i:2d}  {instr}")
        print("─" * 50)
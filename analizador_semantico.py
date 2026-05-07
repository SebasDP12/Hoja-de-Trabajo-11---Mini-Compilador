from tabla_simbolos import TablaSimbolos
from nodes import (
    Programa, Asignacion, Imprimir, Si,
    OperacionBinaria, Numero, Variable,
    Bloque, Declaracion, Funcion,
)

# Mapa de tipos para inferir el tipo de un valor Python
def _tipo_de_valor(valor):
    if isinstance(valor, float):
        return "float"
    if isinstance(valor, bool):
        return "int"
    if isinstance(valor, int):
        return "int"
    return "desconocido"


class AnalizadorSemantico:
    def __init__(self):
        self.ambito_global = TablaSimbolos("global")
        self.ambito_actual = self.ambito_global

        self.errores: list[str] = []
        self.advertencias: list[str] = []


    def visitar(self, nodo):
        metodo = getattr(self, f"visitar_{type(nodo).__name__}", None)
        if metodo is None:
            raise Exception(f"Nodo no soportado: {type(nodo).__name__}")
        return metodo(nodo)


    def _error(self, msg: str):
        self.errores.append(f"[ERROR]   {msg}")

    def _advertencia(self, msg: str):
        self.advertencias.append(f"[AVISO]   {msg}")

    def _abrir(self, nombre: str):
        self.ambito_actual = self.ambito_actual.abrir_ambito(nombre)

    def _cerrar(self):
        self.ambito_actual = self.ambito_actual.cerrar_ambito()

    def _verificar_tipos(self, tipo_destino: str, tipo_origen: str, contexto: str):
        if tipo_destino != tipo_origen:
            self._error(
                f"Incompatibilidad de tipos en '{contexto}': "
                f"se esperaba '{tipo_destino}' pero se obtuvo '{tipo_origen}'."
            )


    def visitar_Programa(self, nodo):
        for sentencia in nodo.sentencias:
            self.visitar(sentencia)

    def visitar_Asignacion(self, nodo):
        valor = self.visitar(nodo.valor)
        try:
            info = self.ambito_actual.obtener(nodo.nombre)
            tipo_destino = info["tipo"]
            tipo_origen = _tipo_de_valor(valor)
            self._verificar_tipos(tipo_destino, tipo_origen,
                                  f"{nodo.nombre} = ...")
            self.ambito_actual.asignar(nodo.nombre, valor)
        except Exception:
            self.ambito_actual.simbolos[nodo.nombre] = {
                "tipo": _tipo_de_valor(valor), "valor": valor
            }
            self.ambito_actual.historial.append(
                f"  [IMPL]     {nodo.nombre} = {valor}  (ámbito: {self.ambito_actual.nombre})"
            )
        return valor

    def visitar_Imprimir(self, nodo):
        try:
            valor = self.visitar(nodo.valor)
            return valor
        except Exception as e:
            self._error(str(e))

    def visitar_Si(self, nodo):
        condicion = self.visitar(nodo.condicion)
        if condicion:
            self._abrir("si-entonces")
            for sentencia in nodo.cuerpo:
                self.visitar(sentencia)
            self._cerrar()

    def visitar_OperacionBinaria(self, nodo):
        izq = self.visitar(nodo.izquierda)
        der = self.visitar(nodo.derecha)
        if nodo.operador == "+":  return izq + der
        elif nodo.operador == "-": return izq - der
        elif nodo.operador == "*": return izq * der
        elif nodo.operador == "/": return (izq // der if isinstance(izq, int) and isinstance(der, int) else izq / der)
        elif nodo.operador == ">": return izq > der
        elif nodo.operador == "<": return izq < der

    def visitar_Numero(self, nodo):
        return nodo.valor

    def visitar_Variable(self, nodo):
        try:
            val = self.ambito_actual.obtener(nodo.nombre)["valor"]
            if isinstance(val, str):
                return 0
            return val if val is not None else 0
        except Exception as e:
            self._error(str(e))
            return 0


    def visitar_Declaracion(self, nodo):
        """int/float nombre = expr;"""
        valor = self.visitar(nodo.valor) if nodo.valor else None
        tipo_inferido = _tipo_de_valor(valor) if valor is not None else nodo.tipo

        try:
            info_padre = self.ambito_actual.padre.obtener(nodo.nombre) if self.ambito_actual.padre else None
            if info_padre:
                self._advertencia(
                    f"Shadowing: '{nodo.nombre}' ({nodo.tipo}, ámbito '{self.ambito_actual.nombre}') "
                    f"oculta '{nodo.nombre}' ({info_padre['tipo']}, ámbito padre)."
                )
        except Exception:
            pass

        if valor is not None:
            self._verificar_tipos(nodo.tipo, tipo_inferido,
                                  f"declaración de '{nodo.nombre}'")

        try:
            self.ambito_actual.declarar(nodo.nombre, nodo.tipo, valor)
        except Exception as e:
            self._error(str(e))

        return valor

    def visitar_Bloque(self, nodo):
        """{ sentencias } → abre y cierra un nuevo ámbito"""
        self._abrir("bloque {}")
        for sentencia in nodo.sentencias:
            self.visitar(sentencia)
        self._cerrar()

    def visitar_Funcion(self, nodo):
        """void/int nombre(params) { cuerpo }"""
        self.ambito_actual.simbolos[nodo.nombre] = {
            "tipo": f"funcion:{nodo.tipo_retorno}", "valor": None
        }
        self._abrir(f"función {nodo.nombre}(...)")
        for tipo_p, nombre_p in nodo.parametros:
            self.ambito_actual.declarar(nombre_p, tipo_p, valor="param")
        for sentencia in nodo.cuerpo.sentencias:
            self.visitar(sentencia)
        self._cerrar()


    def imprimir_resumen_final(self):
        print("\n" + "═" * 60)
        print("  RESUMEN FINAL — ANALIZADOR SEMÁNTICO")
        print("═" * 60)

        print("\n▶ HISTORIAL DE ÁMBITOS:")
        for linea in self.ambito_global.historial:
            print(linea)

        print("\n▶ TABLA DE SÍMBOLOS — ÁMBITO GLOBAL (al finalizar):")
        self.ambito_global.imprimir()

        print("\n▶ ERRORES SEMÁNTICOS DETECTADOS:")
        if self.errores:
            for e in self.errores:
                print(f"  ✗ {e}")
        else:
            print("  (ninguno)")

        print("\n▶ ADVERTENCIAS (shadowing, etc.):")
        if self.advertencias:
            for a in self.advertencias:
                print(f"  ⚠ {a}")
        else:
            print("  (ninguna)")

        print("═" * 60 + "\n")


    @property
    def tabla_simbolos(self) -> dict:
        """
        Devuelve un dict plano {nombre: valor} del ámbito global
        para mantener compatibilidad con el main original que imprime
        semantico.tabla_simbolos.
        """
        return {k: v["valor"] for k, v in self.ambito_global.simbolos.items()}
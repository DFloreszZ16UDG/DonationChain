""" 
Actividad 3.1 - Cadena de Bloques (basada en el código de la Actividad 2.4)
Proyecto: Plataforma de transparencia y trazabilidad de donaciones

Ampliaciones respecto a la Actividad 2.4:
- Botón "Consultar campaña": muestra la trazabilidad de una campaña
  (donaciones y gastos en orden, con el saldo tras cada operación).
- Botón "Simular alteración": modifica a propósito un dato registrado
  para comprobar que la verificación de integridad detecta el cambio.
  El mismo botón permite restaurar el dato original.

Este programa es una SIMULACIÓN ACADÉMICA de una Blockchain.
No utiliza una red Blockchain real ni criptomonedas.

Flujo simulado:
Donante selecciona campaña -> donación -> registro de recursos ->
gasto -> comprobante generado -> hash SHA-256 -> validación ->
bloque -> Blockchain -> historial consultable.

El programa genera automáticamente los comprobantes en lugar de
solicitar al usuario que suba un archivo.
"""

import hashlib
import json
import os
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox


CARPETA_COMPROBANTES = "comprobantes"


# ============================================================
# FUNCIONES CRIPTOGRÁFICAS
# ============================================================

def calcular_hash_archivo(ruta):
    """Calcula el hash SHA-256 de un archivo."""
    sha256 = hashlib.sha256()

    with open(ruta, "rb") as archivo:
        while True:
            bloque = archivo.read(4096)
            if not bloque:
                break
            sha256.update(bloque)

    return sha256.hexdigest()


def calcular_hash_datos(datos):
    """Genera SHA-256 a partir de un diccionario de datos."""
    texto = json.dumps(datos, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ============================================================
# COMPROBANTE
# ============================================================

def generar_comprobante(operacion):
    """
    Genera automáticamente un comprobante de la operación.
    El archivo se crea a partir de los datos de la operación.
    """

    os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)

    nombre_archivo = f"comprobante_{operacion.id}.txt"
    ruta = os.path.join(CARPETA_COMPROBANTES, nombre_archivo)

    if operacion.tipo == "DONACION":
        titulo = "COMPROBANTE DE DONACIÓN"
        detalle = "Aportación a la campaña seleccionada"
        persona = f"Donante: {operacion.persona}"
    else:
        titulo = "COMPROBANTE DE GASTO"
        detalle = operacion.concepto
        persona = f"Responsable: {operacion.persona}"

    contenido = (
        f"{titulo}\n"
        "=======================\n\n"
        f"ID de operación: {operacion.id}\n"
        f"Tipo: {operacion.tipo}\n"
        f"{persona}\n"
        f"Campaña: {operacion.campania}\n"
        f"Monto: ${operacion.monto:,.2f} MXN\n"
        f"Fecha: {operacion.fecha}\n"
        f"Concepto: {detalle}\n\n"
        "Este comprobante fue generado automáticamente por el sistema.\n"
    )

    with open(ruta, "w", encoding="utf-8") as archivo:
        archivo.write(contenido)

    return ruta


# ============================================================
# OPERACIÓN
# ============================================================

class Operacion:
    """
    Representa una donación o un gasto que será registrado
    en la Blockchain simulada.
    """

    def __init__(
        self,
        tipo,
        persona,
        campania,
        monto,
        concepto
    ):
        self.id = (
            ("DON-" if tipo == "DONACION" else "GAS-")
            + uuid.uuid4().hex[:8].upper()
        )

        self.tipo = tipo
        self.persona = persona
        self.campania = campania
        self.monto = monto
        self.concepto = concepto
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.ruta_comprobante = ""
        self.hash_comprobante = ""

        # El comprobante se genera automáticamente.
        self.ruta_comprobante = generar_comprobante(self)
        self.hash_comprobante = calcular_hash_archivo(
            self.ruta_comprobante
        )

        # Hash de la información completa de la operación.
        self.hash_operacion = calcular_hash_datos(self.datos())

    def datos(self):
        """Devuelve los datos principales de la operación."""

        return {
            "id": self.id,
            "tipo": self.tipo,
            "persona": self.persona,
            "campania": self.campania,
            "monto": self.monto,
            "concepto": self.concepto,
            "fecha": self.fecha,
            "hash_comprobante": self.hash_comprobante
        }

    def validar(self):
        """Valida los datos y la integridad de la operación."""

        if not self.persona.strip():
            return False, "El nombre del responsable/donante está vacío."

        if not self.campania.strip():
            return False, "La campaña está vacía."

        if self.monto <= 0:
            return False, "El monto debe ser mayor que cero."

        if not self.concepto.strip():
            return False, "El concepto de la operación está vacío."

        if not os.path.exists(self.ruta_comprobante):
            return False, "No se encontró el comprobante generado."

        hash_comprobante_actual = calcular_hash_archivo(
            self.ruta_comprobante
        )

        if hash_comprobante_actual != self.hash_comprobante:
            return False, "La integridad del comprobante fue alterada."

        hash_actual = calcular_hash_datos(self.datos())

        if hash_actual != self.hash_operacion:
            return False, "La integridad de la operación fue alterada."

        return True, "Operación válida."


# ============================================================
# BLOQUE
# ============================================================

class Bloque:
    """Representa un bloque simplificado de la Blockchain."""

    def __init__(self, numero, operaciones, hash_anterior):
        self.numero = numero
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.operaciones = operaciones
        self.hash_anterior = hash_anterior
        self.hash = self.calcular_hash()

    def calcular_hash(self):
        """Calcula el hash del bloque."""

        datos = {
            "numero": self.numero,
            "fecha": self.fecha,
            "operaciones": [
                operacion.datos()
                for operacion in self.operaciones
            ],
            "hash_anterior": self.hash_anterior
        }

        return calcular_hash_datos(datos)


# ============================================================
# BLOCKCHAIN SIMPLIFICADA
# ============================================================

class Blockchain:
    """Gestiona la cadena de bloques del proyecto."""

    def __init__(self):
        self.cadena = []
        self.crear_bloque_genesis()

    def crear_bloque_genesis(self):
        """Crea el primer bloque de la cadena."""

        bloque_genesis = Bloque(
            numero=0,
            operaciones=[],
            hash_anterior="0"
        )

        self.cadena.append(bloque_genesis)

    def ultimo_bloque(self):
        """Devuelve el último bloque registrado."""

        return self.cadena[-1]

    def obtener_operaciones(self):
        """Devuelve todas las operaciones registradas."""

        operaciones = []

        for bloque in self.cadena:
            operaciones.extend(bloque.operaciones)

        return operaciones

    def campania_existe(self, campania):
        """
        Comprueba que exista al menos una donación registrada
        para la campaña.
        """

        for operacion in self.obtener_operaciones():
            if (
                operacion.tipo == "DONACION"
                and operacion.campania.lower() == campania.lower()
            ):
                return True

        return False

    def saldo_campania(self, campania):
        """Calcula el saldo disponible de una campaña."""

        saldo = 0

        for operacion in self.obtener_operaciones():
            if operacion.campania.lower() == campania.lower():
                if operacion.tipo == "DONACION":
                    saldo += operacion.monto
                elif operacion.tipo == "GASTO":
                    saldo -= operacion.monto

        return saldo

    def operaciones_campania(self, campania):
        """
        Devuelve una lista de (bloque, operación) de una campaña,
        en el orden en que fueron registradas.
        """

        registros = []

        for bloque in self.cadena:
            for operacion in bloque.operaciones:
                if operacion.campania.lower() == campania.lower():
                    registros.append((bloque, operacion))

        return registros

    def registrar_operacion(self, operacion):
        """
        Valida la operación y, si es correcta, la registra
        dentro de un nuevo bloque.
        """

        valida, mensaje = operacion.validar()

        if not valida:
            return False, mensaje

        if operacion.tipo == "GASTO":
            if not self.campania_existe(operacion.campania):
                return (
                    False,
                    "No se puede registrar el gasto porque "
                    "la campaña no tiene donaciones registradas."
                )

            saldo = self.saldo_campania(operacion.campania)

            if operacion.monto > saldo:
                return (
                    False,
                    f"El gasto excede el saldo disponible. "
                    f"Saldo actual: ${saldo:,.2f} MXN."
                )

        bloque = Bloque(
            numero=len(self.cadena),
            operaciones=[operacion],
            hash_anterior=self.ultimo_bloque().hash
        )

        self.cadena.append(bloque)

        return True, "Operación validada y registrada correctamente."

    def verificar_integridad(self):
        """Comprueba hashes, comprobantes y enlaces entre bloques."""

        for i in range(1, len(self.cadena)):
            bloque_actual = self.cadena[i]
            bloque_anterior = self.cadena[i - 1]

            if bloque_actual.hash != bloque_actual.calcular_hash():
                return False, f"El bloque {i} fue alterado."

            if bloque_actual.hash_anterior != bloque_anterior.hash:
                return False, (
                    f"El enlace del bloque {i} con el bloque anterior "
                    "fue alterado."
                )

            for operacion in bloque_actual.operaciones:
                if not os.path.exists(operacion.ruta_comprobante):
                    return False, (
                        f"No se encontró el comprobante de "
                        f"{operacion.id}."
                    )

                hash_actual = calcular_hash_archivo(
                    operacion.ruta_comprobante
                )

                if hash_actual != operacion.hash_comprobante:
                    return False, (
                        f"El comprobante de {operacion.id} "
                        "fue alterado."
                    )

                hash_operacion_actual = calcular_hash_datos(
                    operacion.datos()
                )

                if hash_operacion_actual != operacion.hash_operacion:
                    return False, (
                        f"La operación {operacion.id} "
                        "fue alterada."
                    )

        return True, "La Blockchain mantiene su integridad."


# ============================================================
# INTERFAZ GRÁFICA
# ============================================================

class Aplicacion(tk.Tk):
    """Ventana principal del programa."""

    def __init__(self):
        super().__init__()

        self.title("Blockchain - Transparencia de Donaciones")
        self.geometry("980x720")
        self.minsize(880, 650)

        self.blockchain = Blockchain()

        # Guarda (operación, monto original) mientras hay una
        # alteración simulada activa.
        self.alteracion = None

        self.crear_interfaz()

    def crear_interfaz(self):
        """Construye los elementos gráficos principales."""

        titulo = ttk.Label(
            self,
            text="Plataforma de Transparencia y Trazabilidad de Donaciones",
            font=("Arial", 16, "bold")
        )
        titulo.pack(pady=15)

        marco_datos = ttk.LabelFrame(
            self,
            text="Registrar operación",
            padding=15
        )
        marco_datos.pack(fill="x", padx=20, pady=10)

        ttk.Label(
            marco_datos,
            text="Tipo de operación:"
        ).grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.tipo_operacion = ttk.Combobox(
            marco_datos,
            values=["DONACION", "GASTO"],
            state="readonly",
            width=18
        )
        self.tipo_operacion.set("DONACION")
        self.tipo_operacion.grid(
            row=0, column=1, sticky="w", padx=10, pady=5
        )

        self.tipo_operacion.bind(
            "<<ComboboxSelected>>",
            self.actualizar_etiquetas
        )

        self.etiqueta_persona = ttk.Label(
            marco_datos,
            text="Donante:"
        )
        self.etiqueta_persona.grid(
            row=1, column=0, sticky="w", pady=5
        )

        self.entrada_persona = ttk.Entry(
            marco_datos,
            width=45
        )
        self.entrada_persona.grid(
            row=1, column=1, sticky="w", padx=10, pady=5
        )

        ttk.Label(
            marco_datos,
            text="Campaña:"
        ).grid(
            row=2, column=0, sticky="w", pady=5
        )

        self.entrada_campania = ttk.Entry(
            marco_datos,
            width=45
        )
        self.entrada_campania.grid(
            row=2, column=1, sticky="w", padx=10, pady=5
        )

        ttk.Label(
            marco_datos,
            text="Monto (MXN):"
        ).grid(
            row=3, column=0, sticky="w", pady=5
        )

        self.entrada_monto = ttk.Entry(
            marco_datos,
            width=20
        )
        self.entrada_monto.grid(
            row=3, column=1, sticky="w", padx=10, pady=5
        )

        self.etiqueta_concepto = ttk.Label(
            marco_datos,
            text="Concepto:"
        )
        self.etiqueta_concepto.grid(
            row=4, column=0, sticky="w", pady=5
        )

        self.entrada_concepto = ttk.Entry(
            marco_datos,
            width=45
        )
        self.entrada_concepto.grid(
            row=4, column=1, sticky="w", padx=10, pady=5
        )

        self.boton_registrar = ttk.Button(
            marco_datos,
            text="Validar, generar comprobante y registrar",
            command=self.registrar_operacion
        )
        self.boton_registrar.grid(
            row=5, column=0, columnspan=2, pady=10
        )

        marco_acciones = ttk.Frame(self)
        marco_acciones.pack(fill="x", padx=20, pady=5)

        ttk.Button(
            marco_acciones,
            text="Mostrar Blockchain",
            command=self.mostrar_blockchain
        ).pack(side="left", padx=5)

        ttk.Button(
            marco_acciones,
            text="Verificar integridad",
            command=self.verificar_integridad
        ).pack(side="left", padx=5)

        ttk.Button(
            marco_acciones,
            text="Mostrar saldos",
            command=self.mostrar_saldos
        ).pack(side="left", padx=5)

        ttk.Button(
            marco_acciones,
            text="Consultar campaña",
            command=self.consultar_campania
        ).pack(side="left", padx=5)

        self.boton_alteracion = ttk.Button(
            marco_acciones,
            text="Simular alteración",
            command=self.simular_alteracion
        )
        self.boton_alteracion.pack(side="left", padx=5)

        ttk.Button(
            marco_acciones,
            text="Limpiar campos",
            command=self.limpiar
        ).pack(side="left", padx=5)

        marco_resultado = ttk.LabelFrame(
            self,
            text="Resultado",
            padding=10
        )
        marco_resultado.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=10
        )

        self.texto_resultado = tk.Text(
            marco_resultado,
            wrap="word",
            font=("Consolas", 10)
        )
        self.texto_resultado.pack(
            fill="both",
            expand=True
        )

        self.escribir_resultado(
            "Sistema iniciado.\n"
            "La Blockchain contiene el bloque génesis.\n\n"
            "Flujo de la práctica:\n"
            "Donación → Recepción/registro → Gasto → "
            "Comprobante generado → Hash SHA-256 → Validación → "
            "Bloque → Blockchain → Historial"
        )

    def actualizar_etiquetas(self, evento=None):
        """Actualiza los textos según el tipo de operación."""

        if self.tipo_operacion.get() == "DONACION":
            self.etiqueta_persona.config(text="Donante:")
            self.etiqueta_concepto.config(text="Concepto:")
        else:
            self.etiqueta_persona.config(text="Responsable:")
            self.etiqueta_concepto.config(text="Concepto del gasto:")

    def registrar_operacion(self):
        """
        Recopila los datos, genera el comprobante, calcula sus hashes,
        valida la operación y la registra en un bloque.
        """

        if self.alteracion is not None:
            messagebox.showwarning(
                "Alteración activa",
                "Restaura el dato original antes de registrar "
                "nuevas operaciones."
            )
            return

        tipo = self.tipo_operacion.get()
        persona = self.entrada_persona.get().strip()
        campania = self.entrada_campania.get().strip()
        monto_texto = self.entrada_monto.get().strip()
        concepto = self.entrada_concepto.get().strip()

        if not persona or not campania or not monto_texto or not concepto:
            messagebox.showwarning(
                "Datos incompletos",
                "Completa todos los campos."
            )
            return

        try:
            monto = float(monto_texto)
        except ValueError:
            messagebox.showwarning(
                "Monto inválido",
                "El monto debe ser un número."
            )
            return

        if monto <= 0:
            messagebox.showwarning(
                "Monto inválido",
                "El monto debe ser mayor que cero."
            )
            return

        try:
            operacion = Operacion(
                tipo=tipo,
                persona=persona,
                campania=campania,
                monto=monto,
                concepto=concepto
            )

            exito, mensaje = self.blockchain.registrar_operacion(
                operacion
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No fue posible registrar la operación:\n{error}"
            )
            return

        if exito:
            bloque = self.blockchain.ultimo_bloque()
            saldo = self.blockchain.saldo_campania(campania)

            self.escribir_resultado(
                "✓ OPERACIÓN VALIDADA Y REGISTRADA\n\n"
                f"Tipo: {operacion.tipo}\n"
                f"ID: {operacion.id}\n"
                f"Persona: {operacion.persona}\n"
                f"Campaña: {operacion.campania}\n"
                f"Monto: ${operacion.monto:,.2f} MXN\n"
                f"Concepto: {operacion.concepto}\n"
                f"Fecha: {operacion.fecha}\n\n"
                "COMPROBANTE GENERADO\n"
                f"Archivo: {operacion.ruta_comprobante}\n\n"
                "SHA-256 DEL COMPROBANTE\n"
                f"{operacion.hash_comprobante}\n\n"
                "HASH DE LA OPERACIÓN\n"
                f"{operacion.hash_operacion}\n\n"
                f"Bloque: {bloque.numero}\n"
                "HASH DEL BLOQUE\n"
                f"{bloque.hash}\n\n"
                f"Saldo de la campaña: ${saldo:,.2f} MXN\n\n"
                "La operación forma parte del historial de la "
                "Blockchain simulada."
            )

            messagebox.showinfo(
                "Operación exitosa",
                "La operación fue validada, el comprobante fue generado "
                "y la operación fue registrada."
            )

            self.limpiar()

        else:
            self.escribir_resultado(
                f"✗ OPERACIÓN RECHAZADA\n\n{mensaje}"
            )

            messagebox.showerror(
                "Operación rechazada",
                mensaje
            )

    def mostrar_blockchain(self):
        """Muestra los bloques y operaciones registrados."""

        self.texto_resultado.delete("1.0", tk.END)

        for bloque in self.blockchain.cadena:
            self.texto_resultado.insert(
                tk.END,
                f"========== BLOQUE {bloque.numero} ==========\n"
            )

            self.texto_resultado.insert(
                tk.END,
                f"Fecha: {bloque.fecha}\n"
            )

            self.texto_resultado.insert(
                tk.END,
                f"Hash anterior: {bloque.hash_anterior}\n"
            )

            self.texto_resultado.insert(
                tk.END,
                f"Hash del bloque: {bloque.hash}\n"
            )

            if not bloque.operaciones:
                self.texto_resultado.insert(
                    tk.END,
                    "Operaciones: Bloque génesis\n\n"
                )
                continue

            for operacion in bloque.operaciones:
                self.texto_resultado.insert(
                    tk.END,
                    "\n--- OPERACIÓN ---\n"
                    f"Tipo: {operacion.tipo}\n"
                    f"ID: {operacion.id}\n"
                    f"Persona: {operacion.persona}\n"
                    f"Campaña: {operacion.campania}\n"
                    f"Monto: ${operacion.monto:,.2f} MXN\n"
                    f"Concepto: {operacion.concepto}\n"
                    f"Fecha: {operacion.fecha}\n"
                    f"Comprobante: {operacion.ruta_comprobante}\n"
                    f"Hash comprobante: {operacion.hash_comprobante}\n"
                    f"Hash operación: {operacion.hash_operacion}\n"
                )

            self.texto_resultado.insert(tk.END, "\n")

    def mostrar_saldos(self):
        """Muestra el saldo disponible de cada campaña registrada."""

        operaciones = self.blockchain.obtener_operaciones()
        campanias = []

        for operacion in operaciones:
            if operacion.campania not in campanias:
                campanias.append(operacion.campania)

        self.texto_resultado.delete("1.0", tk.END)

        if not campanias:
            self.texto_resultado.insert(
                tk.END,
                "No existen campañas con operaciones registradas."
            )
            return

        self.texto_resultado.insert(
            tk.END,
            "========== SALDOS DE CAMPAÑAS ==========\n\n"
        )

        for campania in campanias:
            donado = 0
            gastado = 0

            for operacion in operaciones:
                if operacion.campania == campania:
                    if operacion.tipo == "DONACION":
                        donado += operacion.monto
                    elif operacion.tipo == "GASTO":
                        gastado += operacion.monto

            saldo = donado - gastado

            self.texto_resultado.insert(
                tk.END,
                f"Campaña: {campania}\n"
                f"Total recibido: ${donado:,.2f} MXN\n"
                f"Total gastado: ${gastado:,.2f} MXN\n"
                f"Saldo disponible: ${saldo:,.2f} MXN\n\n"
            )

    def verificar_integridad(self):
        """Comprueba la integridad de bloques, operaciones y comprobantes."""

        valido, mensaje = self.blockchain.verificar_integridad()

        if valido:
            self.escribir_resultado(
                "✓ INTEGRIDAD VERIFICADA\n\n"
                f"{mensaje}\n\n"
                "Los hashes de los bloques coinciden con su contenido, "
                "los comprobantes coinciden con sus hashes, las "
                "operaciones coinciden con sus hashes y los enlaces "
                "entre bloques son correctos."
            )

            messagebox.showinfo(
                "Integridad",
                mensaje
            )

        else:
            self.escribir_resultado(
                f"✗ ALERTA DE INTEGRIDAD\n\n{mensaje}"
            )

            messagebox.showwarning(
                "Integridad",
                mensaje
            )

    def consultar_campania(self):
        """
        Muestra la trazabilidad de una campaña: sus donaciones y
        gastos en orden, con el bloque y el saldo tras cada operación.
        """

        campania = self.entrada_campania.get().strip()

        if not campania:
            messagebox.showwarning(
                "Campaña vacía",
                "Escribe el nombre de la campaña en el campo "
                "'Campaña' para consultar su trazabilidad."
            )
            return

        registros = self.blockchain.operaciones_campania(campania)

        if not registros:
            self.escribir_resultado(
                f"No hay operaciones registradas para la campaña "
                f"'{campania}'."
            )
            return

        donado = 0
        gastado = 0

        texto = (
            "========== TRAZABILIDAD DE LA CAMPAÑA: "
            f"{registros[0][1].campania} ==========\n\n"
        )

        for bloque, operacion in registros:
            if operacion.tipo == "DONACION":
                donado += operacion.monto
                etiqueta = "DONACIÓN"
                rol = "Donante"
            else:
                gastado += operacion.monto
                etiqueta = "GASTO"
                rol = "Responsable"

            texto += (
                f"[Bloque {bloque.numero}] {etiqueta} - {operacion.id}\n"
                f"  Fecha: {operacion.fecha}\n"
                f"  {rol}: {operacion.persona}\n"
                f"  Monto: ${operacion.monto:,.2f} MXN\n"
                f"  Concepto: {operacion.concepto}\n"
                f"  Hash del comprobante: "
                f"{operacion.hash_comprobante[:16]}...\n"
                f"  Saldo tras la operación: "
                f"${donado - gastado:,.2f} MXN\n\n"
            )

        texto += (
            "RESUMEN\n"
            f"Total recibido: ${donado:,.2f} MXN\n"
            f"Total gastado: ${gastado:,.2f} MXN\n"
            f"Saldo disponible: ${donado - gastado:,.2f} MXN"
        )

        self.escribir_resultado(texto)

    def simular_alteracion(self):
        """
        Alterna entre alterar a propósito el monto de la última
        operación registrada (solo en memoria) y restaurar el
        valor original. Sirve para demostrar que la verificación
        de integridad detecta cualquier cambio.
        """

        if self.alteracion is None:
            operaciones = self.blockchain.obtener_operaciones()

            if not operaciones:
                messagebox.showwarning(
                    "Sin operaciones",
                    "Registra al menos una operación para poder "
                    "simular una alteración."
                )
                return

            operacion = operaciones[-1]
            monto_original = operacion.monto

            self.alteracion = (operacion, monto_original)
            operacion.monto = monto_original + 1000

            self.boton_alteracion.config(text="Restaurar dato original")

            self.escribir_resultado(
                "⚠ ALTERACIÓN SIMULADA\n\n"
                f"Se modificó el monto de la operación {operacion.id} "
                f"de ${monto_original:,.2f} MXN a "
                f"${operacion.monto:,.2f} MXN.\n"
                "El cambio es solo en memoria y no se recalcularon "
                "los hashes.\n\n"
                "Ahora pulsa 'Verificar integridad' para comprobar "
                "que la alteración es detectada."
            )

        else:
            operacion, monto_original = self.alteracion
            operacion.monto = monto_original

            self.alteracion = None
            self.boton_alteracion.config(text="Simular alteración")

            self.escribir_resultado(
                "✓ DATO RESTAURADO\n\n"
                f"El monto de la operación {operacion.id} volvió a "
                f"${monto_original:,.2f} MXN.\n\n"
                "Pulsa 'Verificar integridad' para comprobar que la "
                "cadena vuelve a ser válida."
            )

    def limpiar(self):
        """Limpia los campos para registrar otra operación."""

        self.entrada_persona.delete(0, tk.END)
        self.entrada_campania.delete(0, tk.END)
        self.entrada_monto.delete(0, tk.END)
        self.entrada_concepto.delete(0, tk.END)

    def escribir_resultado(self, texto):
        """Actualiza el área de resultados."""

        self.texto_resultado.delete("1.0", tk.END)
        self.texto_resultado.insert(tk.END, texto)


# ============================================================
# INICIO DEL PROGRAMA
# ============================================================

if __name__ == "__main__":
    app = Aplicacion()
    app.mainloop()

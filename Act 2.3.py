"""
Actividad 2.3 - Cadena de Bloques
Proyecto: Plataforma de transparencia y trazabilidad de donaciones

Este programa es una SIMULACIÓN ACADÉMICA de una Blockchain.
No utiliza una red Blockchain real ni criptomonedas.

Desarrollo personal:
- Se diseñó una interfaz gráfica con Tkinter.
- Se incorporó la selección de un comprobante desde el equipo.
- Se implementó SHA-256 para obtener la huella digital del comprobante.
- Se implementó la creación y validación de transacciones.
- Se implementó una cadena de bloques simplificada.
- Se agregó una función para comprobar la integridad de la cadena.

La estructura general se basa en los conceptos estudiados en la actividad,
pero la implementación, interfaz y lógica de este programa fueron realizadas
específicamente para el proyecto de donaciones.
"""

import hashlib
import json
import math
import os
import uuid
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# ============================================================
# FUNCIONES CRIPTOGRÁFICAS
# ============================================================

def calcular_hash_archivo(ruta):
    """Calcula el hash SHA-256 de un archivo seleccionado."""
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
# TRANSACCIÓN
# ============================================================

class Transaccion:
    """Representa una donación que será registrada en Blockchain."""

    def __init__(self, donante, campania, monto, hash_comprobante):
        self.id = "DON-" + uuid.uuid4().hex[:8].upper()
        self.donante = donante
        self.campania = campania
        self.monto = monto
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.hash_comprobante = hash_comprobante

        # Hash de la información completa de la transacción.
        datos = self.datos()
        self.hash_transaccion = calcular_hash_datos(datos)

    def datos(self):
        """Devuelve los datos principales de la transacción."""
        return {
            "id": self.id,
            "donante": self.donante,
            "campania": self.campania,
            "monto": self.monto,
            "fecha": self.fecha,
            "hash_comprobante": self.hash_comprobante
        }

    def validar(self):
        """
        Valida los datos básicos de la transacción.

        Esta validación representa de forma simplificada la etapa
        'Validar transacción' del diagrama.
        """
        if not isinstance(self.donante, str) or not self.donante.strip():
            return False, "El nombre del donante está vacío."

        if not isinstance(self.campania, str) or not self.campania.strip():
            return False, "La campaña está vacía."

        if (
            isinstance(self.monto, bool)
            or not isinstance(self.monto, (int, float))
        ):
            return False, "El monto debe ser un número finito."

        if isinstance(self.monto, float) and not math.isfinite(self.monto):
            return False, "El monto debe ser un número finito."

        if self.monto <= 0:
            return False, "El monto debe ser mayor que cero."

        if round(self.monto, 2) != self.monto:
            return False, "El monto puede tener como máximo dos decimales."

        if (
            not isinstance(self.hash_comprobante, str)
            or len(self.hash_comprobante) != 64
            or any(
                caracter not in "0123456789abcdefABCDEF"
                for caracter in self.hash_comprobante
            )
        ):
            return False, "El hash del comprobante no es un SHA-256 válido."

        # Recalculamos el hash para comprobar que los datos no cambiaron.
        hash_actual = calcular_hash_datos(self.datos())

        if hash_actual != self.hash_transaccion:
            return False, "La integridad de la transacción fue alterada."

        return True, "Transacción válida."


# ============================================================
# BLOQUE
# ============================================================

class Bloque:
    """Representa un bloque simplificado de la Blockchain."""

    def __init__(self, numero, transacciones, hash_anterior):
        self.numero = numero
        self.fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.transacciones = transacciones
        self.hash_anterior = hash_anterior

        # El hash identifica criptográficamente el contenido del bloque.
        self.hash = self.calcular_hash()

    def calcular_hash(self):
        """Calcula el hash del bloque."""
        datos = {
            "numero": self.numero,
            "fecha": self.fecha,
            "transacciones": [
                {
                    "datos": transaccion.datos(),
                    "hash_transaccion": transaccion.hash_transaccion
                }
                for transaccion in self.transacciones
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
            transacciones=[],
            hash_anterior="0"
        )
        self.cadena.append(bloque_genesis)

    def ultimo_bloque(self):
        """Devuelve el último bloque registrado."""
        return self.cadena[-1]

    def registrar_transaccion(self, transaccion):
        """
        Valida la transacción y, si es correcta, la registra
        dentro de un nuevo bloque.
        """
        valida, mensaje = transaccion.validar()

        if not valida:
            return False, mensaje

        bloque = Bloque(
            numero=len(self.cadena),
            transacciones=[transaccion],
            hash_anterior=self.ultimo_bloque().hash
        )

        self.cadena.append(bloque)

        return True, "Transacción validada y registrada correctamente."

    def verificar_integridad(self):
        """
        Comprueba que los hashes y enlaces entre bloques
        sigan siendo válidos.
        """
        if not self.cadena:
            return False, "La Blockchain no contiene un bloque génesis."

        for i, bloque_actual in enumerate(self.cadena):
            if bloque_actual.numero != i:
                return False, f"La numeración del bloque {i} fue alterada."

            # Verifica que el hash almacenado corresponda al contenido.
            try:
                hash_calculado = bloque_actual.calcular_hash()
            except (AttributeError, TypeError, ValueError):
                return False, f"El bloque {i} contiene datos inválidos."

            if bloque_actual.hash != hash_calculado:
                return False, f"El bloque {i} fue alterado."

            # Verifica también la integridad propia de cada transacción.
            for transaccion in bloque_actual.transacciones:
                valida, _ = transaccion.validar()
                if not valida:
                    return False, (
                        f"Una transacción del bloque {i} fue alterada."
                    )

            if i == 0:
                if bloque_actual.hash_anterior != "0":
                    return False, "El enlace del bloque génesis fue alterado."
                if bloque_actual.transacciones:
                    return False, "El bloque génesis contiene transacciones."
                continue

            # Verifica el enlace con el bloque anterior.
            bloque_anterior = self.cadena[i - 1]
            if bloque_actual.hash_anterior != bloque_anterior.hash:
                return False, (
                    f"El enlace del bloque {i} con el bloque anterior "
                    "fue alterado."
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
        self.geometry("900x650")
        self.minsize(800, 600)

        self.blockchain = Blockchain()
        self.ruta_comprobante = ""
        self.hash_comprobante = ""

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
            text="Registrar donación",
            padding=15
        )
        marco_datos.pack(fill="x", padx=20, pady=10)

        ttk.Label(marco_datos, text="Donante:").grid(
            row=0, column=0, sticky="w", pady=5
        )

        self.entrada_donante = ttk.Entry(marco_datos, width=45)
        self.entrada_donante.grid(
            row=0, column=1, sticky="w", padx=10, pady=5
        )

        ttk.Label(marco_datos, text="Campaña:").grid(
            row=1, column=0, sticky="w", pady=5
        )

        self.entrada_campania = ttk.Entry(marco_datos, width=45)
        self.entrada_campania.grid(
            row=1, column=1, sticky="w", padx=10, pady=5
        )

        ttk.Label(marco_datos, text="Monto (MXN):").grid(
            row=2, column=0, sticky="w", pady=5
        )

        self.entrada_monto = ttk.Entry(marco_datos, width=20)
        self.entrada_monto.grid(
            row=2, column=1, sticky="w", padx=10, pady=5
        )

        self.boton_comprobante = ttk.Button(
            marco_datos,
            text="Seleccionar comprobante",
            command=self.seleccionar_comprobante
        )
        self.boton_comprobante.grid(
            row=3, column=0, padx=5, pady=10, sticky="w"
        )

        self.etiqueta_comprobante = ttk.Label(
            marco_datos,
            text="Ningún comprobante seleccionado."
        )
        self.etiqueta_comprobante.grid(
            row=3, column=1, sticky="w", padx=10
        )

        self.boton_registrar = ttk.Button(
            marco_datos,
            text="Validar y registrar donación",
            command=self.registrar_donacion
        )
        self.boton_registrar.grid(
            row=4, column=0, columnspan=2, pady=10
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
            "Donación → Hash → Transacción → Validación → "
            "Bloque → Blockchain → Confirmación"
        )

    def seleccionar_comprobante(self):
        """Permite seleccionar un archivo y calcula su hash SHA-256."""

        ruta = filedialog.askopenfilename(
            title="Seleccionar comprobante"
        )

        if not ruta:
            return

        try:
            self.ruta_comprobante = ruta
            self.hash_comprobante = calcular_hash_archivo(ruta)

            nombre = os.path.basename(ruta)

            self.etiqueta_comprobante.config(
                text=f"{nombre} | SHA-256: {self.hash_comprobante[:16]}..."
            )

            self.escribir_resultado(
                "Comprobante seleccionado correctamente.\n\n"
                f"Archivo: {nombre}\n"
                f"SHA-256: {self.hash_comprobante}\n\n"
                "El archivo permanece fuera de la Blockchain. "
                "Solo su hash será incluido en la transacción."
            )

        except Exception as error:
            messagebox.showerror(
                "Error",
                f"No fue posible procesar el comprobante:\n{error}"
            )

    def registrar_donacion(self):
        """
        Recopila los datos, crea una transacción, la valida
        y la registra en un nuevo bloque.
        """

        donante = self.entrada_donante.get().strip()
        campania = self.entrada_campania.get().strip()
        monto_texto = self.entrada_monto.get().strip()

        # Validación de los datos introducidos por el usuario.
        if not donante or not campania or not monto_texto:
            messagebox.showwarning(
                "Datos incompletos",
                "Completa donante, campaña y monto."
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

        if not math.isfinite(monto):
            messagebox.showwarning(
                "Monto inválido",
                "El monto debe ser un número finito."
            )
            return

        if monto <= 0:
            messagebox.showwarning(
                "Monto inválido",
                "El monto debe ser mayor que cero."
            )
            return

        if round(monto, 2) != monto:
            messagebox.showwarning(
                "Monto inválido",
                "El monto puede tener como máximo dos decimales."
            )
            return

        if not self.hash_comprobante:
            messagebox.showwarning(
                "Comprobante faltante",
                "Selecciona un comprobante antes de registrar la donación."
            )
            return

        # Se crea la transacción con los datos de la donación.
        transaccion = Transaccion(
            donante=donante,
            campania=campania,
            monto=monto,
            hash_comprobante=self.hash_comprobante
        )

        # Se valida y registra la transacción en un bloque.
        exito, mensaje = self.blockchain.registrar_transaccion(
            transaccion
        )

        if exito:
            bloque = self.blockchain.ultimo_bloque()

            self.escribir_resultado(
                "✓ TRANSACCIÓN VALIDADA Y REGISTRADA\n\n"
                f"ID de donación: {transaccion.id}\n"
                f"Donante: {transaccion.donante}\n"
                f"Campaña: {transaccion.campania}\n"
                f"Monto: ${transaccion.monto:,.2f} MXN\n"
                f"Fecha: {transaccion.fecha}\n\n"
                f"Hash del comprobante:\n"
                f"{transaccion.hash_comprobante}\n\n"
                f"Hash de la transacción:\n"
                f"{transaccion.hash_transaccion}\n\n"
                f"Bloque: {bloque.numero}\n"
                f"Hash del bloque:\n{bloque.hash}\n\n"
                "La donación ahora forma parte del historial "
                "de la Blockchain simulada."
            )

            messagebox.showinfo(
                "Operación exitosa",
                "La transacción fue validada y registrada."
            )

            self.limpiar()

        else:
            self.escribir_resultado(
                f"✗ TRANSACCIÓN RECHAZADA\n\n{mensaje}"
            )

            messagebox.showerror(
                "Transacción rechazada",
                mensaje
            )

    def mostrar_blockchain(self):
        """Muestra los bloques registrados actualmente."""

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

            if not bloque.transacciones:
                self.texto_resultado.insert(
                    tk.END,
                    "Transacciones: Bloque génesis\n\n"
                )
                continue

            for transaccion in bloque.transacciones:
                self.texto_resultado.insert(
                    tk.END,
                    "\n--- TRANSACCIÓN ---\n"
                    f"ID: {transaccion.id}\n"
                    f"Donante: {transaccion.donante}\n"
                    f"Campaña: {transaccion.campania}\n"
                    f"Monto: ${transaccion.monto:,.2f} MXN\n"
                    f"Fecha: {transaccion.fecha}\n"
                    f"Hash comprobante: {transaccion.hash_comprobante}\n"
                    f"Hash transacción: {transaccion.hash_transaccion}\n"
                )

            self.texto_resultado.insert(tk.END, "\n")

    def verificar_integridad(self):
        """Comprueba la integridad de todos los bloques."""

        valido, mensaje = self.blockchain.verificar_integridad()

        if valido:
            self.escribir_resultado(
                "✓ INTEGRIDAD VERIFICADA\n\n"
                f"{mensaje}\n\n"
                "Los hashes de los bloques coinciden con su contenido "
                "y los enlaces entre bloques son correctos."
            )
            messagebox.showinfo("Integridad", mensaje)
        else:
            self.escribir_resultado(
                f"✗ ALERTA DE INTEGRIDAD\n\n{mensaje}"
            )
            messagebox.showwarning("Integridad", mensaje)

    def limpiar(self):
        """Limpia los campos para registrar otra donación."""

        self.entrada_donante.delete(0, tk.END)
        self.entrada_campania.delete(0, tk.END)
        self.entrada_monto.delete(0, tk.END)

        self.ruta_comprobante = ""
        self.hash_comprobante = ""

        self.etiqueta_comprobante.config(
            text="Ningún comprobante seleccionado."
        )

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

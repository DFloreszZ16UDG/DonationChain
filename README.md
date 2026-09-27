# Plataforma de transparencia de donaciones con Blockchain

## Descripción

Este proyecto es una simulación académica de una plataforma de transparencia y trazabilidad de donaciones mediante una cadena de bloques.

El programa permite registrar una donación, calcular la huella digital de su comprobante, validar los datos de la transacción y almacenarla dentro de una Blockchain simplificada.

No utiliza criptomonedas ni se conecta a una red Blockchain real. Su propósito es demostrar de manera visual conceptos como transacciones, validación, hashes, bloques, encadenamiento e integridad de la información.

## Objetivo

Utilizar los principios de Blockchain para crear un historial verificable de donaciones.

El sistema busca representar cómo una organización podría registrar movimientos importantes y utilizar hashes criptográficos para detectar modificaciones en las transacciones o sus comprobantes.

## Funcionalidades

- Registro del nombre del donante.
- Registro de la campaña beneficiada.
- Registro del monto de la donación.
- Selección de un comprobante desde el equipo.
- Cálculo del hash SHA-256 del comprobante.
- Creación de un identificador único para cada donación.
- Generación del hash de la transacción.
- Validación de los datos antes del registro.
- Creación de bloques enlazados mediante hashes.
- Visualización de la Blockchain.
- Verificación de la integridad de bloques y transacciones.
- Detección de modificaciones en la información registrada.

## Flujo de una transacción

El flujo principal del programa es:

```text
Ingresar datos de la donación
        ↓
Seleccionar comprobante
        ↓
Calcular hash SHA-256 del comprobante
        ↓
Crear transacción
        ↓
Calcular hash de la transacción
        ↓
Validar transacción
        ↓
Crear un nuevo bloque
        ↓
Enlazar con el bloque anterior
        ↓
Calcular hash del bloque
        ↓
Agregar bloque a la Blockchain
        ↓
Mostrar confirmación
```

## Tipos de hash utilizados

### Hash del comprobante

Representa la huella digital del archivo seleccionado. Permite comprobar si el comprobante fue modificado posteriormente.

### Hash de la transacción

Protege los datos de la donación, incluyendo el donante, la campaña, el monto, la fecha y el hash del comprobante.

### Hash del bloque

Protege el contenido completo del bloque y permite enlazarlo con el siguiente bloque de la cadena.

## Tecnologías utilizadas

- Python 3
- Tkinter
- SHA-256
- JSON
- UUID

Todas las bibliotecas utilizadas forman parte de la biblioteca estándar de Python, por lo que no es necesario instalar paquetes adicionales.

## Requisitos

- Python 3.8 o posterior.
- Tkinter disponible en la instalación de Python.

Para comprobar que Python está instalado:

```bash
python --version
```

## Ejecución

1. Descargar o clonar este repositorio.
2. Abrir una terminal dentro de la carpeta del proyecto.
3. Ejecutar:

```bash
python "Act 2.3.py"
```

## Uso

1. Escribir el nombre del donante.
2. Escribir el nombre de la campaña.
3. Introducir el monto de la donación.
4. Seleccionar un archivo como comprobante.
5. Presionar **Validar y registrar donación**.
6. Consultar los bloques con **Mostrar Blockchain**.
7. Comprobar la cadena con **Verificar integridad**.

El comprobante puede ser un archivo PDF, una imagen o un documento de texto. El archivo no se almacena dentro de la Blockchain; únicamente se registra su hash SHA-256.

## Alcance y limitaciones

Este programa es una simulación local con fines educativos.

Actualmente:

- La Blockchain se mantiene únicamente mientras el programa está abierto.
- La información no se guarda en una base de datos.
- No existe comunicación entre nodos.
- No se utiliza un mecanismo de consenso.
- No se emplean firmas digitales.
- No se realizan transferencias de criptomonedas.
- Cada donación se registra en un bloque independiente.
- No se verifica que una transferencia bancaria haya ocurrido realmente.

Los hashes permiten detectar modificaciones, pero no demuestran por sí solos que un comprobante sea auténtico.

## Posibles mejoras

- Crear campañas con metas de recaudación.
- Registrar gastos asociados con cada campaña.
- Calcular las cantidades recaudadas, utilizadas y disponibles.
- Incorporar usuarios y roles.
- Agregar firmas digitales.
- Guardar la cadena en un archivo o base de datos.
- Permitir la verificación posterior de comprobantes.
- Mostrar un historial completo por campaña.
- Incorporar una red de nodos para simular un sistema distribuido.

## Propósito académico

Proyecto desarrollado para la materia **Cadena de Bloques**, con el objetivo de representar el flujo de creación, validación y registro de una transacción dentro de una Blockchain simplificada.

## Autores

- Nombres: `Diego Flores Murillo, Diego Alexis Galván Roldán`
- Carrera: Ingeniería en Informática
- Materia: Cadena de Bloques

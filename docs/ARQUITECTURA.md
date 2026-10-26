# Arquitectura de DonationChain

## Objetivo

DonationChain permite que una persona consulte cómo se recibió y utilizó una donación. La base de datos conserva los datos operativos y los archivos; Blockchain conserva únicamente huellas criptográficas que permiten detectar cambios.

## Componentes

```text
Navegador (React + TypeScript)
              |
              | HTTPS / JSON / archivos
              v
API (FastAPI + autorización por roles)
       |              |                |
       v              v                v
 Base de datos   Comprobantes      Adaptador Web3
   SQLite        PDF/JPG/PNG             |
   o PostgreSQL    + SHA-256              v
                                  Smart Contract
                                  Ethereum Sepolia
                                  Proof of Stake
```

## Responsabilidades

- **Frontend:** presenta campañas, saldos, trazabilidad, formularios y revisión de gastos. No contiene reglas financieras críticas.
- **API:** autentica, aplica permisos, valida `Decimal`, limita archivos, calcula SHA-256 y ejecuta las reglas de negocio.
- **Base de datos:** almacena usuarios, organizaciones, campañas, donaciones, gastos, asignaciones y auditoría.
- **Almacenamiento:** conserva los comprobantes fuera de Blockchain.
- **Contrato:** ancla `recordId`, `dataHash`, tipo, fecha, escritor y URI lógica. No almacena nombres, comprobantes ni dinero.

## Flujo real de un gasto

1. Una organización envía concepto, monto exacto y comprobante.
2. La API valida tipo, tamaño, firma mágica del archivo y SHA-256.
3. El gasto queda `PENDING`; todavía no reduce el saldo.
4. Un auditor o administrador revisa y aprueba o rechaza.
5. Al aprobar, se comprueba el saldo y se asignan donaciones al gasto mediante FIFO.
6. Se crea una entrada de auditoría enlazada con el hash anterior.
7. Si el contrato está configurado, un administrador puede anclar esa entrada en Sepolia.
8. La vista pública actualiza el total utilizado y muestra la huella del comprobante.

## Flujo de una donación y su acuse

1. El donante registra una aportación para una campaña activa.
2. La API conserva el monto exacto, el folio y la relación con el usuario.
3. Se crea una entrada de auditoría con un hash SHA-256 enlazado al registro anterior.
4. El donante descarga un acuse PDF con los datos y el hash de evidencia.
5. El administrador ancla la entrada en el Smart Contract de Sepolia.
6. La plataforma consulta el contrato y comprueba que el hash local coincida con el almacenado en Blockchain.
7. El donante puede abrir la transacción en el explorador de Sepolia.

## Modelo de confianza

Blockchain detecta alteraciones posteriores, pero no demuestra por sí sola que una factura sea auténtica. La autenticidad inicial depende de la revisión, la identidad de la organización y, en un despliegue real, validaciones fiscales o bancarias adicionales.

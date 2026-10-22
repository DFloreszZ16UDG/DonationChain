# Seguridad y límites del piloto

## Controles implementados

- Contraseñas con `scrypt`, sal aleatoria y comparación constante.
- Sesiones mediante JWT con expiración.
- Roles `ADMIN`, `ORGANIZATION`, `DONOR` y `AUDITOR`.
- Montos con `Decimal` y dos decimales; no se usa `float`.
- Comprobantes limitados a 10 MB y a PDF, PNG o JPEG detectados por contenido.
- Nombres almacenados aleatorios; se elimina cualquier ruta incluida en el nombre original.
- SHA-256 para comprobar integridad de archivos.
- Gastos pendientes hasta aprobación independiente.
- Prevención de sobregiro y de asignaciones mayores que donaciones o gastos.
- Auditoría encadenada mediante `previous_hash` y `entry_hash`.
- Contrato con escritores autorizados, IDs no repetibles y transferencia de propiedad en dos pasos.
- Secretos y archivos subidos excluidos de Git.

## Verificaciones automatizadas

`test-all.ps1` ejecuta:

- pruebas integrales de API;
- análisis estático con Ruff y Bandit;
- auditoría de dependencias Python con pip-audit;
- compilación de producción del frontend;
- auditoría de dependencias npm;
- compilación y pruebas del Smart Contract.

## Antes de producción

- Cambiar SQLite por PostgreSQL administrado y usar migraciones.
- Guardar comprobantes en almacenamiento privado cifrado con respaldos.
- Usar HTTPS, cookies `HttpOnly` o un proveedor de identidad; añadir MFA a administradores.
- Aplicar rate limiting, antivirus de archivos, CSP y monitoreo centralizado.
- Rotar secretos en un gestor; nunca colocar una clave privada en Git.
- Realizar revisión legal de privacidad, conservación de archivos y comprobantes fiscales.
- Someter el contrato a auditoría externa antes de usar una red principal.
- Implementar conciliación bancaria; un hash no demuestra que el pago sucedió.

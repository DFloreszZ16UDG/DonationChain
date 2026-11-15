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
- Límite de intentos de inicio de sesión por usuario e IP en cada instancia.
- Cabeceras contra interpretación de contenido, iframes y permisos del navegador.
- Validación de hosts y redirección HTTPS configurable.
- Bloqueo transaccional de la cadena de auditoría cuando se usa PostgreSQL.
- Restricciones positivas de montos y tamaños también en la base de datos.
- Almacenamiento compatible con S3 usando cifrado del lado del servidor.

## Verificaciones automatizadas

`test-all.ps1` ejecuta:

- pruebas integrales de API;
- análisis estático con Ruff y Bandit;
- auditoría de dependencias Python con pip-audit;
- compilación de producción del frontend;
- auditoría de dependencias npm;
- compilación y pruebas del Smart Contract.

## Preparado para el piloto publicado

- PostgreSQL dispone de controlador y migraciones Alembic.
- Los comprobantes pueden guardarse en un volumen persistente o bucket privado compatible con S3.
- La pila de contenedores incluye frontend, API, PostgreSQL, comprobaciones de salud y proxy Nginx.
- El administrador inicial se crea mediante consola y no mediante una ruta pública.
- GitHub Actions repite las pruebas y auditorías en cada cambio.

## Pendiente antes de manejar dinero real

- Usar HTTPS en el proveedor, cookies `HttpOnly` o un proveedor de identidad; añadir MFA a administradores.
- Sustituir el limitador local por Redis al ejecutar varias instancias.
- Aplicar antivirus de archivos, CSP y monitoreo centralizado.
- Rotar secretos en un gestor; nunca colocar una clave privada en Git.
- Realizar revisión legal de privacidad, conservación de archivos y comprobantes fiscales.
- Someter el contrato a auditoría externa antes de usar una red principal.
- Implementar conciliación bancaria; un hash no demuestra que el pago sucedió.

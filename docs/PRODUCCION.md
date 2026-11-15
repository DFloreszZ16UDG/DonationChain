# Despliegue de DonationChain

El repositorio puede ejecutarse localmente como antes o como una pila de producción reproducible con PostgreSQL, migraciones, almacenamiento persistente y un proxy web.

## Preparación

1. Copiar `.env.compose.example` como `.env` y asignar una contraseña larga a PostgreSQL.
2. Generar un `JWT_SECRET` aleatorio de al menos 48 caracteres.
3. Configurar los dominios reales en `CORS_ORIGINS` y `TRUSTED_HOSTS`.
4. Configurar el contrato de Sepolia y guardar la clave privada únicamente como secreto del servidor.

El archivo `.env` con secretos está ignorado por Git; el archivo `.env.compose.example` solo contiene marcadores y nombres de variables.

## Inicio con contenedores

```bash
docker compose up --build -d
docker compose ps
```

La aplicación queda disponible en `http://localhost:8080`. En un servidor público se debe colocar un proxy o balanceador con TLS delante del puerto 8080.

## Primer administrador

Las cuentas de demostración nunca se crean cuando `ENVIRONMENT=production`. Después de iniciar la base de datos:

```bash
docker compose exec -e INITIAL_ADMIN_PASSWORD="una-clave-segura" backend \
  python -m app.cli create-admin --email admin@example.com --name "Administrador"
```

El comando falla si el correo ya existe y no expone una ruta HTTP de configuración privilegiada.

## Migraciones

El contenedor del backend ejecuta `alembic upgrade head` antes de iniciar la API. Para crear una migración después de modificar los modelos:

```bash
cd backend
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head
```

No se debe utilizar `Base.metadata.create_all()` en producción; `AUTO_CREATE_DATABASE` debe permanecer en `false`.

## Comprobantes

### Volumen persistente

La configuración incluida utiliza `STORAGE_BACKEND=local` y el volumen `receipt_data`. Es adecuada para un piloto de un solo servidor, siempre que el volumen tenga copias de seguridad.

### Almacenamiento de objetos

Para varias instancias o un proveedor cloud se recomienda almacenamiento privado compatible con S3:

```dotenv
STORAGE_BACKEND=s3
S3_BUCKET=donationchain-private
S3_PREFIX=receipts
S3_REGION=us-east-1
S3_ENDPOINT_URL=
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

El bucket no debe ser público. DonationChain descarga los objetos a través de una ruta autenticada para administradores, auditores y organizaciones.

## Operación y respaldos

- Comprobar `/api/health` para disponibilidad del proceso.
- Comprobar `/api/ready` para conexión con PostgreSQL y configuración del almacenamiento.
- Respaldar diariamente PostgreSQL y los comprobantes.
- Conservar registros del servidor fuera del contenedor.
- Rotar `JWT_SECRET`, credenciales de PostgreSQL y la cartera de Sepolia ante cualquier exposición.
- Probar periódicamente la restauración de los respaldos.

## Límites que requieren servicios externos

Publicar esta pila crea un piloto accesible, no una institución financiera. Para recibir dinero real todavía se debe contratar e integrar una pasarela de pago o conciliación bancaria, verificar legalmente a las organizaciones, definir obligaciones fiscales, habilitar correo transaccional, recuperación de contraseña, MFA y políticas de privacidad. Estas funciones no pueden activarse de manera responsable sin elegir proveedores, cuentas y responsables legales.

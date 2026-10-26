# Despliegue del piloto

## Piloto local

1. Ejecutar `./setup.ps1`.
2. Copiar `backend/.env.example` como `backend/.env`.
3. Reemplazar `JWT_SECRET` y `DEMO_PASSWORD` por valores propios.
4. Abrir una terminal y ejecutar `./start-backend.ps1`.
5. Abrir otra terminal y ejecutar `./start-frontend.ps1`.
6. Entrar a `http://localhost:5173`; la documentación de la API queda en `http://127.0.0.1:8000/docs`.

## Conexión Proof of Stake

El piloto consulta Ethereum Sepolia, red de prueba basada en Proof of Stake, con chain ID `11155111`. La lectura funciona sin clave privada. Escribir requiere:

1. Crear una cartera exclusiva para pruebas. Se puede usar `npm run wallet:create` dentro de `contracts/`; el comando guarda la clave solo en el archivo ignorado `contracts/.env` y muestra únicamente la dirección pública.
2. Obtener ETH de prueba desde un faucet confiable.
3. Si no se usó el comando anterior, copiar `contracts/.env.example` como `contracts/.env` y configurar la RPC y clave de prueba solo de forma local.
4. Ejecutar `npm run deploy:sepolia` dentro de `contracts/`; Hardhat carga automáticamente el archivo local `.env`.
5. Ejecutar `npm run configure:backend` para copiar de forma local la dirección desplegada y la clave de la cartera de prueba a `backend/.env`, sin mostrarlas ni subirlas a GitHub.
6. Si se usa otra cuenta para firmar, el propietario debe autorizarla mediante `setWriter`.
7. Reiniciar la API, entrar como administrador y abrir **Auditoría**.
8. Usar **Anclar en Sepolia** y después **Verificar hash**. La interfaz mostrará el enlace de la transacción.

La clave debe pertenecer únicamente a una cuenta de prueba. El contrato no recibe ni transfiere donaciones.

## Despliegue actual de demostración

- Red: Ethereum Sepolia (`11155111`).
- Contrato: [`0x5c1F526eff76983ade86D6981c23d7b9D8E6d597`](https://sepolia.etherscan.io/address/0x5c1F526eff76983ade86D6981c23d7b9D8E6d597).
- Cartera de escritura de prueba: `0xECd71f8213E60586632ADd1B55C4Df6AFfaa7E5D`.
- Transacción de verificación del piloto: [`0x719fd2f623f1c4fa5380102e05c18ac14214b5bf6de16a6d7892e1b9d89b0aed`](https://sepolia.etherscan.io/tx/0x719fd2f623f1c4fa5380102e05c18ac14214b5bf6de16a6d7892e1b9d89b0aed).

La dirección y la transacción son públicas. La clave privada correspondiente permanece exclusivamente en los archivos locales ignorados por Git.

## Publicación en Internet

El frontend puede alojarse como sitio estático. La API requiere un servicio compatible con Python, HTTPS, base de datos PostgreSQL y almacenamiento privado. No publique el frontend por separado apuntando a `localhost`; primero debe existir una URL segura para la API.

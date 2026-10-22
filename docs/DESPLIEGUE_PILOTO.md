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

1. Crear una cartera exclusiva para pruebas.
2. Obtener ETH de prueba desde un faucet confiable.
3. Copiar `contracts/.env.example` como `contracts/.env` y configurar la RPC y clave de prueba solo de forma local.
4. Cargar esas variables en la terminal y ejecutar `npm run deploy:sepolia` dentro de `contracts/`.
5. Copiar la dirección desplegada a `BLOCKCHAIN_CONTRACT_ADDRESS` en `backend/.env`.
6. Configurar `BLOCKCHAIN_PRIVATE_KEY` con una cuenta autorizada mediante `setWriter`.
7. Reiniciar la API y usar `POST /api/blockchain/anchor/{audit_id}` como administrador.

La clave debe pertenecer únicamente a una cuenta de prueba. El contrato no recibe ni transfiere donaciones.

## Publicación en Internet

El frontend puede alojarse como sitio estático. La API requiere un servicio compatible con Python, HTTPS, base de datos PostgreSQL y almacenamiento privado. No publique el frontend por separado apuntando a `localhost`; primero debe existir una URL segura para la API.

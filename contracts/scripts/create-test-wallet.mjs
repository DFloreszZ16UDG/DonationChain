import { existsSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { generatePrivateKey, privateKeyToAccount } from 'viem/accounts'

const envPath = resolve(process.cwd(), '.env')

if (existsSync(envPath)) {
  console.error('contracts/.env ya existe. No se reemplazó la cartera configurada.')
  process.exit(1)
}

const privateKey = generatePrivateKey()
const account = privateKeyToAccount(privateKey)
const contents = [
  'SEPOLIA_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com',
  `SEPOLIA_PRIVATE_KEY=${privateKey}`,
  '',
].join('\n')

writeFileSync(envPath, contents, { encoding: 'utf8', flag: 'wx', mode: 0o600 })

console.log('Cartera de prueba creada. Dirección pública:')
console.log(account.address)
console.log('La clave privada permanece únicamente en contracts/.env y no se mostró.')

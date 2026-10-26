import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { resolve } from 'node:path'

const contractsDir = resolve(import.meta.dirname, '..')
const projectDir = resolve(contractsDir, '..')
const walletEnvPath = resolve(contractsDir, '.env')
const deploymentPath = resolve(
  contractsDir,
  'ignition',
  'deployments',
  'chain-11155111',
  'deployed_addresses.json',
)
const backendEnvPath = resolve(projectDir, 'backend', '.env')
const backendExamplePath = resolve(projectDir, 'backend', '.env.example')

if (!existsSync(walletEnvPath)) {
  throw new Error('Falta contracts/.env. Ejecuta primero: npm run wallet:create')
}
if (!existsSync(deploymentPath)) {
  throw new Error('Falta el despliegue de Sepolia. Ejecuta primero: npm run deploy:sepolia')
}

const walletEnv = readFileSync(walletEnvPath, 'utf8')
const privateKey = walletEnv.match(/^SEPOLIA_PRIVATE_KEY=(.+)$/m)?.[1]?.trim()
if (!privateKey) {
  throw new Error('SEPOLIA_PRIVATE_KEY no está configurada en contracts/.env')
}

const deployments = JSON.parse(readFileSync(deploymentPath, 'utf8'))
const contractEntry = Object.entries(deployments).find(([name]) =>
  name.endsWith('#DonationTraceability'),
)
if (!contractEntry) {
  throw new Error('No se encontró DonationTraceability en el despliegue de Sepolia')
}
const [, contractAddress] = contractEntry

const sourcePath = existsSync(backendEnvPath) ? backendEnvPath : backendExamplePath
let backendEnv = readFileSync(sourcePath, 'utf8')

function setEnvValue(contents, name, value) {
  const line = `${name}=${value}`
  const pattern = new RegExp(`^${name}=.*$`, 'm')
  return pattern.test(contents)
    ? contents.replace(pattern, line)
    : `${contents.trimEnd()}\n${line}\n`
}

backendEnv = setEnvValue(backendEnv, 'BLOCKCHAIN_CONTRACT_ADDRESS', contractAddress)
backendEnv = setEnvValue(backendEnv, 'BLOCKCHAIN_PRIVATE_KEY', privateKey)
writeFileSync(backendEnvPath, backendEnv, { encoding: 'utf8', mode: 0o600 })

console.log(`Contrato configurado en backend/.env: ${contractAddress}`)
console.log('La clave privada se copió localmente y no se mostró en pantalla.')

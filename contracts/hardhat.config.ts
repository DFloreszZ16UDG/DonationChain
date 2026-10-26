import hardhatToolboxViem from '@nomicfoundation/hardhat-toolbox-viem'
import { defineConfig } from 'hardhat/config'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

const envFile = resolve(process.cwd(), '.env')
if (existsSync(envFile)) process.loadEnvFile(envFile)

const sepoliaUrl = process.env.SEPOLIA_RPC_URL
const deployerKey = process.env.SEPOLIA_PRIVATE_KEY

export default defineConfig({
  plugins: [hardhatToolboxViem],
  solidity: {
    profiles: {
      default: {
        version: '0.8.30',
        settings: { optimizer: { enabled: true, runs: 200 } },
      },
      production: {
        version: '0.8.30',
        settings: { optimizer: { enabled: true, runs: 500 } },
      },
    },
  },
  networks: sepoliaUrl && deployerKey ? {
    sepolia: {
      type: 'http',
      chainType: 'l1',
      url: sepoliaUrl,
      accounts: [deployerKey],
    },
  } : {},
})

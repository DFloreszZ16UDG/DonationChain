import hardhatToolboxViem from '@nomicfoundation/hardhat-toolbox-viem'
import { defineConfig } from 'hardhat/config'

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

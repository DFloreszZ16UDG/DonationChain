import { buildModule } from '@nomicfoundation/hardhat-ignition/modules'

export default buildModule('DonationTraceabilityModule', (module) => {
  const donationTraceability = module.contract('DonationTraceability')
  return { donationTraceability }
})

import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { network } from 'hardhat'
import { keccak256, stringToHex, zeroHash } from 'viem'

describe('DonationTraceability', async function () {
  async function deployFixture() {
    const { viem } = await network.create()
    const [owner, writer, outsider] = await viem.getWalletClients()
    const contract = await viem.deployContract('DonationTraceability')
    return { contract, owner, writer, outsider }
  }

  it('anchors and verifies a record', async function () {
    const { contract } = await deployFixture()
    const recordId = keccak256(stringToHex('audit-1'))
    const dataHash = keccak256(stringToHex('canonical-data'))
    await contract.write.anchorRecord([recordId, dataHash, 4, 'donationchain://audit/1'])
    assert.equal(await contract.read.verifyRecord([recordId, dataHash]), true)
    const anchor = await contract.read.getAnchor([recordId])
    assert.equal(anchor.dataHash, dataHash)
    assert.equal(anchor.recordType, 4)
  })

  it('rejects unauthorized writers', async function () {
    const { contract, outsider } = await deployFixture()
    const recordId = keccak256(stringToHex('audit-2'))
    const dataHash = keccak256(stringToHex('data'))
    await assert.rejects(
      contract.write.anchorRecord([recordId, dataHash, 4, 'uri'], { account: outsider.account }),
    )
  })

  it('allows an authorized writer and blocks duplicate IDs', async function () {
    const { contract, writer } = await deployFixture()
    await contract.write.setWriter([writer.account.address, true])
    const recordId = keccak256(stringToHex('audit-3'))
    const dataHash = keccak256(stringToHex('data'))
    await contract.write.anchorRecord([recordId, dataHash, 4, 'uri'], { account: writer.account })
    await assert.rejects(
      contract.write.anchorRecord([recordId, dataHash, 4, 'uri'], { account: writer.account }),
    )
  })

  it('rejects zero hashes', async function () {
    const { contract } = await deployFixture()
    await assert.rejects(contract.write.anchorRecord([zeroHash, zeroHash, 4, 'uri']))
  })
})

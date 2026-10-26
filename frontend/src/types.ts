export type Role = 'ADMIN' | 'ORGANIZATION' | 'DONOR' | 'AUDITOR'

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
  organization_id: string | null
  active: boolean
}

export interface Campaign {
  id: string
  organization_id: string
  name: string
  description: string
  goal_amount: string
  status: 'DRAFT' | 'ACTIVE' | 'COMPLETED'
  created_at: string
  donated: string
  spent: string
  available: string
}

export interface TimelineEvent {
  id: string
  event_type: 'DONATION' | 'EXPENSE'
  title: string
  description: string
  amount: string | null
  status: string
  receipt_id: string | null
  receipt_hash: string | null
  created_at: string
}

export interface Expense {
  id: string
  campaign_id: string
  concept: string
  description: string
  amount: string
  receipt_id: string
  status: 'PENDING' | 'APPROVED' | 'REJECTED'
  created_at: string
}

export interface Donation {
  id: string
  campaign_id: string
  donor_name: string
  amount: string
  receipt_id: string | null
  created_at: string
}

export interface DonationTrace {
  donation: Donation
  campaign_name: string
  allocated: string
  unallocated: string
  audit_id: string | null
  audit_hash: string | null
  anchor_status: string | null
  blockchain_tx_hash: string | null
  blockchain_block_number: number | null
  allocations: Array<{
    allocation_id: string
    expense_id: string
    concept: string
    description: string
    amount: string
    status: string
    created_at: string
  }>
}

export interface AuditEntry {
  id: string
  actor_id: string | null
  action: string
  entity_type: string
  entity_id: string
  entry_hash: string
  previous_hash: string
  anchor_status: string
  blockchain_tx_hash: string | null
  created_at: string
}

export interface BlockchainStatus {
  network: string
  chain_id: number
  rpc_connected: boolean
  latest_block: number | null
  contract_configured: boolean
  writes_enabled: boolean
  explorer_url: string
  message: string
}

export interface BlockchainVerification {
  audit_id: string
  record_id: string
  expected_hash: string
  on_chain_hash: string | null
  anchored: boolean
  matches: boolean
  writer: string | null
  timestamp: number | null
  metadata_uri: string | null
  blockchain_tx_hash: string | null
  blockchain_block_number: number | null
  explorer_url: string
}

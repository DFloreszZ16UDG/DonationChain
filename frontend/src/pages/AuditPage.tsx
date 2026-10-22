import LinkOutlined from '@mui/icons-material/LinkOutlined'
import SecurityOutlined from '@mui/icons-material/SecurityOutlined'
import { Alert, Box, Button, Card, CardContent, Chip, Container, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'
import { api, shortHash } from '../api'
import type { AuditEntry, BlockchainStatus } from '../types'

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([])
  const [verification, setVerification] = useState<{ valid: boolean; message: string } | null>(null)
  const [chain, setChain] = useState<BlockchainStatus | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      api<AuditEntry[]>('/audit?limit=100'),
      api<{ valid: boolean; message: string }>('/audit/verify'),
      api<BlockchainStatus>('/blockchain/status'),
    ]).then(([logs, check, status]) => { setEntries(logs); setVerification(check); setChain(status) }).catch((reason: Error) => setError(reason.message))
  }, [])

  return (
    <Container maxWidth="lg" sx={{ py: 7 }}>
      <Typography variant="overline" color="primary" fontWeight={800}>Evidencia verificable</Typography>
      <Typography variant="h2" sx={{ fontSize: { xs: '2.3rem', md: '3.3rem' } }}>Historial de auditoría</Typography>
      <Typography color="text.secondary" sx={{ mb: 4 }}>Cada entrada incluye el hash anterior. Modificar una rompe la verificación de toda la cadena posterior.</Typography>
      {error ? <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert> : null}
      <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mb: 4 }}>
        <Alert icon={<SecurityOutlined />} severity={verification?.valid ? 'success' : 'warning'} sx={{ flex: 1 }}>{verification?.message ?? 'Verificando cadena…'}</Alert>
        <Alert severity={chain?.rpc_connected ? 'success' : 'info'} sx={{ flex: 1 }}>{chain?.message ?? 'Consultando la red…'}{chain?.latest_block ? ` · bloque ${chain.latest_block.toLocaleString()}` : ''}</Alert>
      </Stack>
      <Stack spacing={1.5}>
        {entries.map((entry) => <Card key={entry.id}><CardContent sx={{ p: 2.5 }}>
          <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}>
            <Box><Stack direction="row" gap={1} alignItems="center"><LinkOutlined color="primary" /><Typography fontWeight={850}>{entry.action.replaceAll('_', ' ')}</Typography><Chip size="small" label={entry.entity_type} /></Stack><Typography variant="body2" color="text.secondary" sx={{ mt: .7 }}>Entidad {shortHash(entry.entity_id, 8)} · {new Date(entry.created_at).toLocaleString('es-MX')}</Typography></Box>
            <Box sx={{ textAlign: { md: 'right' } }}><Typography variant="caption" display="block" title={entry.entry_hash}>Hash {shortHash(entry.entry_hash)}</Typography><Chip size="small" label={entry.anchor_status === 'CONFIRMED' ? 'Anclado en Blockchain' : entry.anchor_status === 'PENDING' ? 'Pendiente de anclaje' : 'Auditoría local'} color={entry.anchor_status === 'CONFIRMED' ? 'success' : 'default'} /></Box>
          </Stack>
          {entry.blockchain_tx_hash && chain ? <Button size="small" href={`${chain.explorer_url}/tx/${entry.blockchain_tx_hash}`} target="_blank" rel="noreferrer" sx={{ mt: 1 }}>Ver transacción</Button> : null}
        </CardContent></Card>)}
      </Stack>
    </Container>
  )
}

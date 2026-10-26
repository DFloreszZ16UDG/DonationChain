"""Read/write integration with the DonationTraceability smart contract."""

from dataclasses import dataclass

from sqlalchemy.orm import Session
from web3 import Web3

from ..config import get_settings
from ..models import AnchorStatus, AuditLog

CONTRACT_ABI = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "recordId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
            {"internalType": "uint8", "name": "recordType", "type": "uint8"},
            {"internalType": "string", "name": "metadataURI", "type": "string"},
        ],
        "name": "anchorRecord",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "bytes32", "name": "recordId", "type": "bytes32"}],
        "name": "getAnchor",
        "outputs": [
            {
                "components": [
                    {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
                    {
                        "internalType": "enum DonationTraceability.RecordType",
                        "name": "recordType",
                        "type": "uint8",
                    },
                    {"internalType": "uint64", "name": "timestamp", "type": "uint64"},
                    {"internalType": "address", "name": "writer", "type": "address"},
                    {"internalType": "string", "name": "metadataURI", "type": "string"},
                ],
                "internalType": "struct DonationTraceability.Anchor",
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "recordId", "type": "bytes32"},
            {"internalType": "bytes32", "name": "dataHash", "type": "bytes32"},
        ],
        "name": "verifyRecord",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]


@dataclass(frozen=True)
class NetworkStatus:
    connected: bool
    latest_block: int | None
    message: str


@dataclass(frozen=True)
class AnchorVerification:
    record_id: str
    on_chain_hash: str | None
    anchored: bool
    matches: bool
    writer: str | None
    timestamp: int | None
    metadata_uri: str | None


def network_status() -> NetworkStatus:
    settings = get_settings()
    if not settings.blockchain_rpc_url:
        return NetworkStatus(False, None, "No hay una URL RPC configurada")
    try:
        web3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url, request_kwargs={"timeout": 5}))
        if not web3.is_connected():
            return NetworkStatus(False, None, "La red de prueba no respondió")
        chain_id = web3.eth.chain_id
        if chain_id != settings.blockchain_chain_id:
            return NetworkStatus(False, None, f"La RPC respondió con chain ID {chain_id}")
        return NetworkStatus(True, web3.eth.block_number, "Conexión de lectura activa con Sepolia")
    except Exception as exc:  # Network failures are reported, not fatal to the API.
        return NetworkStatus(False, None, f"No fue posible consultar la red: {exc}")


def verify_audit_anchor(audit: AuditLog) -> AnchorVerification:
    """Read the Smart Contract and compare its hash with the local audit entry."""

    settings = get_settings()
    if not settings.blockchain_rpc_url or not settings.blockchain_contract_address:
        raise RuntimeError("El Smart Contract todavía no está configurado")
    web3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url, request_kwargs={"timeout": 20}))
    if not web3.is_connected():
        raise RuntimeError("No fue posible conectar con Ethereum Sepolia")
    if web3.eth.chain_id != settings.blockchain_chain_id:
        raise RuntimeError("La RPC configurada no corresponde a Ethereum Sepolia")
    contract = web3.eth.contract(
        address=Web3.to_checksum_address(settings.blockchain_contract_address),
        abi=CONTRACT_ABI,
    )
    record_id_bytes = Web3.keccak(text=audit.id)
    anchor = contract.functions.getAnchor(record_id_bytes).call()
    timestamp = int(anchor[2])
    anchored = timestamp != 0
    on_chain_hash = Web3.to_hex(anchor[0])[2:] if anchored else None
    expected = bytes.fromhex(audit.entry_hash)
    matches = bool(contract.functions.verifyRecord(record_id_bytes, expected).call())
    return AnchorVerification(
        record_id=Web3.to_hex(record_id_bytes),
        on_chain_hash=on_chain_hash,
        anchored=anchored,
        matches=matches,
        writer=anchor[3] if anchored else None,
        timestamp=timestamp if anchored else None,
        metadata_uri=anchor[4] if anchored else None,
    )


def anchor_audit_entry(db: Session, audit: AuditLog) -> AuditLog:
    settings = get_settings()
    if not settings.blockchain_writes_enabled:
        raise RuntimeError("Faltan dirección del contrato o clave de firma")

    try:
        web3 = Web3(Web3.HTTPProvider(settings.blockchain_rpc_url, request_kwargs={"timeout": 20}))
        account = web3.eth.account.from_key(settings.blockchain_private_key)
        contract = web3.eth.contract(
            address=Web3.to_checksum_address(settings.blockchain_contract_address),
            abi=CONTRACT_ABI,
        )
        record_id = Web3.keccak(text=audit.id)
        data_hash = bytes.fromhex(audit.entry_hash)
        transaction = contract.functions.anchorRecord(
            record_id,
            data_hash,
            4,
            f"donationchain://audit/{audit.id}",
        ).build_transaction(
            {
                "from": account.address,
                "nonce": web3.eth.get_transaction_count(account.address),
                "chainId": settings.blockchain_chain_id,
            }
        )
        transaction["gas"] = web3.eth.estimate_gas(transaction)
        transaction["maxPriorityFeePerGas"] = web3.to_wei(1, "gwei")
        transaction["maxFeePerGas"] = web3.eth.gas_price * 2
        signed = account.sign_transaction(transaction)
        tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        if receipt.status != 1:
            raise RuntimeError("La transacción fue revertida")
        audit.anchor_status = AnchorStatus.CONFIRMED
        audit.blockchain_tx_hash = tx_hash.hex()
        audit.blockchain_block_number = receipt.blockNumber
    except Exception:
        audit.anchor_status = AnchorStatus.FAILED
        db.add(audit)
        db.commit()
        raise
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit

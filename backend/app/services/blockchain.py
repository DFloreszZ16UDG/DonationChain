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
    }
]


@dataclass(frozen=True)
class NetworkStatus:
    connected: bool
    latest_block: int | None
    message: str


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

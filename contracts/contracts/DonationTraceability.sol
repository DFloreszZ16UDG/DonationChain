// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

/// @title DonationTraceability
/// @notice Anchors hashes from DonationChain without storing files, names or monetary assets.
/// @dev This contract is an evidence registry; it is not a payment processor or source of truth.
contract DonationTraceability {
    enum RecordType {
        Campaign,
        Donation,
        Expense,
        Allocation,
        Audit
    }

    struct Anchor {
        bytes32 dataHash;
        RecordType recordType;
        uint64 timestamp;
        address writer;
        string metadataURI;
    }

    error Unauthorized();
    error AlreadyAnchored(bytes32 recordId);
    error InvalidHash();
    error ZeroAddress();

    address public owner;
    address public pendingOwner;
    mapping(address => bool) public authorizedWriters;
    mapping(bytes32 => Anchor) private anchors;

    event RecordAnchored(
        bytes32 indexed recordId,
        bytes32 indexed dataHash,
        RecordType indexed recordType,
        address writer,
        string metadataURI
    );
    event WriterAuthorizationChanged(address indexed writer, bool authorized);
    event OwnershipTransferStarted(address indexed currentOwner, address indexed pendingOwner);
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);

    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    modifier onlyWriter() {
        if (!authorizedWriters[msg.sender]) revert Unauthorized();
        _;
    }

    constructor() {
        owner = msg.sender;
        authorizedWriters[msg.sender] = true;
        emit WriterAuthorizationChanged(msg.sender, true);
        emit OwnershipTransferred(address(0), msg.sender);
    }

    function setWriter(address writer, bool authorized) external onlyOwner {
        if (writer == address(0)) revert ZeroAddress();
        authorizedWriters[writer] = authorized;
        emit WriterAuthorizationChanged(writer, authorized);
    }

    function beginOwnershipTransfer(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert ZeroAddress();
        pendingOwner = newOwner;
        emit OwnershipTransferStarted(owner, newOwner);
    }

    function acceptOwnership() external {
        if (msg.sender != pendingOwner) revert Unauthorized();
        address previousOwner = owner;
        owner = msg.sender;
        pendingOwner = address(0);
        authorizedWriters[msg.sender] = true;
        emit WriterAuthorizationChanged(msg.sender, true);
        emit OwnershipTransferred(previousOwner, msg.sender);
    }

    function anchorRecord(
        bytes32 recordId,
        bytes32 dataHash,
        uint8 recordType,
        string calldata metadataURI
    ) external onlyWriter {
        if (recordId == bytes32(0) || dataHash == bytes32(0)) revert InvalidHash();
        if (anchors[recordId].timestamp != 0) revert AlreadyAnchored(recordId);
        if (recordType > uint8(RecordType.Audit)) revert InvalidHash();

        anchors[recordId] = Anchor({
            dataHash: dataHash,
            recordType: RecordType(recordType),
            timestamp: uint64(block.timestamp),
            writer: msg.sender,
            metadataURI: metadataURI
        });
        emit RecordAnchored(recordId, dataHash, RecordType(recordType), msg.sender, metadataURI);
    }

    function getAnchor(bytes32 recordId) external view returns (Anchor memory) {
        return anchors[recordId];
    }

    function verifyRecord(bytes32 recordId, bytes32 dataHash) external view returns (bool) {
        Anchor storage anchor = anchors[recordId];
        return anchor.timestamp != 0 && anchor.dataHash == dataHash;
    }
}

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract MedicalImageProvenance {
    struct ProvenanceRecord {
        string imageHash;
        string metadataJSON;
        uint256 timestamp;
        address recorder;
        uint256 blockNumber;
    }

    // imageHash => array of provenance records
    mapping(string => ProvenanceRecord[]) public provenanceHistory;

    event ProvenanceRecorded(
        string indexed imageHash,
        address indexed recorder,
        uint256 timestamp
    );

    function recordProvenance(
        string memory imageHash,
        string memory metadataJSON
    ) public {
        ProvenanceRecord memory record = ProvenanceRecord({
            imageHash: imageHash,
            metadataJSON: metadataJSON,
            timestamp: block.timestamp,
            recorder: msg.sender,
            blockNumber: block.number
        });

        provenanceHistory[imageHash].push(record);

        emit ProvenanceRecorded(imageHash, msg.sender, block.timestamp);
    }

    function getProvenanceCount(string memory imageHash)
        public
        view
        returns (uint256)
    {
        return provenanceHistory[imageHash].length;
    }

    function getProvenance(string memory imageHash, uint256 index)
        public
        view
        returns (
            string memory metadataJSON,
            uint256 timestamp,
            address recorder,
            uint256 blockNumber
        )
    {
        require(index < provenanceHistory[imageHash].length, "Index out of bounds");
        ProvenanceRecord memory record = provenanceHistory[imageHash][index];
        return (
            record.metadataJSON,
            record.timestamp,
            record.recorder,
            record.blockNumber
        );
    }
}

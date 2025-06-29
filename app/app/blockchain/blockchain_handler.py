"""
Blockchain handler for the Smart Learning with Personalized AI Tutor application
"""

import json
import hashlib
from web3 import Web3
from eth_account.messages import encode_defunct
from flask import current_app

class BlockchainHandler:
    """Handler for blockchain operations"""
    
    def __init__(self):
        """Initialize blockchain handler"""
        self.web3 = None
        self.contract = None
        
        # Initialize Web3 if not in mock mode
        if not current_app.config.get('MOCK_BLOCKCHAIN', False):
            try:
                self.web3 = Web3(Web3.HTTPProvider(current_app.config['WEB3_PROVIDER_URI']))
                # Here you would initialize your smart contract
                # self.contract = self.web3.eth.contract(
                #     address=current_app.config['CONTRACT_ADDRESS'],
                #     abi=YOUR_CONTRACT_ABI
                # )
            except Exception as e:
                print(f"Warning: Could not initialize blockchain connection: {str(e)}")
    
    def get_hash(self, data):
        """
        Generate a hash for data verification
        
        Args:
            data (dict): Data to hash
            
        Returns:
            str: Hash of the data
        """
        # Convert data to JSON string
        json_str = json.dumps(data, sort_keys=True)
        
        # Generate SHA-256 hash
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def verify_data(self, data, hash_value):
        """
        Verify data against its hash
        
        Args:
            data (dict): Data to verify
            hash_value (str): Hash to verify against
            
        Returns:
            bool: True if verification succeeds, False otherwise
        """
        return self.get_hash(data) == hash_value
    
    def store_data(self, data):
        """
        Store data on the blockchain
        
        Args:
            data (dict): Data to store
            
        Returns:
            str: Transaction hash or mock hash
        """
        if current_app.config.get('MOCK_BLOCKCHAIN', False):
            # In mock mode, just return a hash
            return self.get_hash(data)
        
        if not self.web3 or not self.contract:
            # If blockchain is not available, just return a hash
            return self.get_hash(data)
        
        try:
            # Here you would implement actual blockchain storage
            # For example:
            # tx_hash = self.contract.functions.storeData(
            #     self.get_hash(data),
            #     json.dumps(data)
            # ).transact()
            # return tx_hash.hex()
            return self.get_hash(data)  # Placeholder
        except Exception as e:
            print(f"Warning: Could not store data on blockchain: {str(e)}")
            return self.get_hash(data)  # Fallback to hash only
    
    def is_connected(self):
        """Check if connected to blockchain"""
        return self.web3.isConnected()
    
    def store_data_hash(self, data_hash, user_address, private_key=None):
        """
        Store a data hash on the blockchain
        
        Args:
            data_hash (str): Hash of the data
            user_address (str): Ethereum address of the user
            private_key (str): Private key for signing transactions
            
        Returns:
            str: Transaction hash
        """
        if not self.contract:
            raise ValueError("Contract not initialized")
        
        # If we're in development/testing mode, use a mock transaction
        if not self.is_connected() or not private_key:
            return self._mock_transaction(data_hash)
        
        # Build the transaction
        nonce = self.web3.eth.getTransactionCount(user_address)
        tx = self.contract.functions.storeDataHash(data_hash).buildTransaction({
            'from': user_address,
            'gas': 2000000,
            'gasPrice': self.web3.toWei('50', 'gwei'),
            'nonce': nonce
        })
        
        # Sign and send the transaction
        signed_tx = self.web3.eth.account.signTransaction(tx, private_key)
        tx_hash = self.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        
        return self.web3.toHex(tx_hash)
    
    def sign_message(self, message, private_key):
        """
        Sign a message with a private key
        
        Args:
            message (str): Message to sign
            private_key (str): Private key for signing
            
        Returns:
            str: Signature
        """
        message_encoded = encode_defunct(text=message)
        signed_message = self.web3.eth.account.sign_message(message_encoded, private_key=private_key)
        return signed_message.signature.hex()
    
    def verify_signature(self, message, signature, address):
        """
        Verify a signature
        
        Args:
            message (str): Original message
            signature (str): Signature to verify
            address (str): Address of the signer
            
        Returns:
            bool: True if the signature is valid
        """
        message_encoded = encode_defunct(text=message)
        recovered_address = self.web3.eth.account.recover_message(message_encoded, signature=signature)
        return recovered_address.lower() == address.lower()
    
    def _mock_transaction(self, data_hash):
        """
        Create a mock transaction for testing
        
        Args:
            data_hash (str): Hash of the data
            
        Returns:
            str: Mock transaction hash
        """
        # Create a deterministic but unique mock transaction hash
        mock_tx = hashlib.sha256(f"{data_hash}_{current_app.config['CONTRACT_ADDRESS']}".encode()).hexdigest()
        return f"0x{mock_tx}"

# Sample smart contract code (Solidity) for reference
"""
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SecureLearningData {
    address public owner;
    
    // Mapping from user address to their data hashes
    mapping(address => string[]) private userDataHashes;
    
    // Events
    event DataHashStored(address indexed user, string dataHash, uint256 timestamp);
    
    constructor() {
        owner = msg.sender;
    }
    
    // Store a data hash
    function storeDataHash(string memory dataHash) public {
        userDataHashes[msg.sender].push(dataHash);
        emit DataHashStored(msg.sender, dataHash, block.timestamp);
    }
    
    // Get all data hashes for a user
    function getUserDataHashes(address user) public view returns (string[] memory) {
        require(msg.sender == user || msg.sender == owner, "Not authorized");
        return userDataHashes[user];
    }
    
    // Verify if a hash exists for a user
    function verifyDataHash(address user, string memory dataHash) public view returns (bool) {
        string[] memory hashes = userDataHashes[user];
        for (uint i = 0; i < hashes.length; i++) {
            if (keccak256(bytes(hashes[i])) == keccak256(bytes(dataHash))) {
                return true;
            }
        }
        return false;
    }
}
""" 
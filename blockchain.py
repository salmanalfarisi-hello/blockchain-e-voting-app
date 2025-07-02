import hashlib
import json
import time
import pickle
import os
from datetime import datetime
from typing import List, Dict, Any

class Transaction:
    def __init__(self, voter_id: str, candidate: str, jurusan: str, timestamp: float = None):
        self.voter_id = voter_id
        self.candidate = candidate
        self.jurusan = jurusan
        self.timestamp = timestamp or time.time()
        self.hash = self.calculate_hash()  # Use consistent naming
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'voter_id': self.voter_id,
            'candidate': self.candidate,
            'jurusan': self.jurusan,
            'timestamp': self.timestamp,
            'tx_hash': self.hash,  # Gunakan tx_hash untuk konsistensi dengan frontend
            'hash': self.hash      # Tetap pertahankan hash untuk kompatibilitas
        }
    
    def calculate_hash(self) -> str:
        """Calculate hash without including the hash itself"""
        data = {
            'voter_id': self.voter_id,
            'candidate': self.candidate,
            'jurusan': self.jurusan,
            'timestamp': self.timestamp
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
class Block:
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str, nonce: int = 0):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate SHA256 hash of the block data"""
        block_data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int):
        """Mine the block with the given difficulty"""
        target = "0" * difficulty
        start_time = time.time()
        
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        end_time = time.time()
        print(f"⛏️  Block #{self.index} mined in {end_time - start_time:.2f}s")
        print(f"🔗 Hash: {self.hash}")

class Blockchain:
    def __init__(self):
        self.chain_file = 'blockchain.dat'
        self.voters_file = 'voters.dat'
        self.chain = self._load_chain() or [self._create_genesis_block()]
        self.difficulty = 3
        self.pending_transactions = []
        self.voters = self._load_voters() or set()
    
    def _create_genesis_block(self) -> Block:
        """Create the genesis block"""
        genesis_block = Block(0, [], "0")
        print("🎯 Genesis block created")
        return genesis_block
    
    def _load_chain(self) -> List[Block]:
        """Load blockchain from file with validation"""
        if os.path.exists(self.chain_file):
            try:
                with open(self.chain_file, 'rb') as f:
                    chain = pickle.load(f)
                    if self._validate_chain(chain):
                        return chain
                    print("⚠️ Loaded invalid chain, creating new one")
                    return None
            except (pickle.PickleError, EOFError, Exception) as e:
                print(f"⚠️ Error loading chain: {str(e)}, creating new one")
                return None
        return None
    
    def _load_voters(self) -> set:
        """Load voters from file"""
        if os.path.exists(self.voters_file):
            try:
                with open(self.voters_file, 'rb') as f:
                    return pickle.load(f)
            except (pickle.PickleError, EOFError, Exception) as e:
                print(f"⚠️ Error loading voters: {str(e)}, creating new set")
                return None
        return None
    
    def _validate_chain(self, chain: List[Block]) -> bool:
        """Validate the integrity of the blockchain"""
        if not chain:
            return False
            
        # Validate genesis block
        genesis = chain[0]
        if (genesis.index != 0 or 
            genesis.previous_hash != "0" or 
            genesis.transactions):
            return False
            
        # Validate subsequent blocks
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            
            # Check current block hash
            if current.hash != current.calculate_hash():
                return False
                
            # Check link to previous block
            if current.previous_hash != previous.hash:
                return False
                
            # Validate all transactions in block
            for tx in current.transactions:
                if not isinstance(tx, Transaction):
                    return False
                if tx.hash != tx.calculate_hash():
                    return False
                    
        return True
    
    def save_state(self):
        """Save the current state to files"""
        try:
            with open(self.chain_file, 'wb') as f:
                pickle.dump(self.chain, f)
            with open(self.voters_file, 'wb') as f:
                pickle.dump(self.voters, f)
        except Exception as e:
            print(f"⚠️ Error saving state: {str(e)}")

    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a new transaction to pending transactions"""
        if not isinstance(transaction, Transaction):
            raise ValueError("Invalid transaction object")
        
        # Verify transaction hash
        if transaction.hash != transaction.calculate_hash():
            print("⚠️ Invalid transaction hash!")
            return False
        
        # Check if voter has already voted
        if self.has_voted(transaction.voter_id):
            print("⚠️ Voter already voted!")
            return False
        
        self.pending_transactions.append(transaction)
        self.voters.add(transaction.voter_id)
        self.save_state()
        return True
        
    def mine_pending_transactions(self) -> bool:
        """Mine all pending transactions into a new block"""
        if not self.pending_transactions:
            print("⚠️ No transactions to mine!")
            return False
        
        print(f"⛏️  Mining block with {len(self.pending_transactions)} transactions...")
        
        block = Block(
            len(self.chain),
            self.pending_transactions.copy(),
            self.get_latest_block().hash
        )
        block.mine_block(self.difficulty)
        
        self.chain.append(block)
        self.pending_transactions = []
        self.save_state()
        
        print(f"✅ Block #{block.index} added to blockchain")
        return True
    
    def has_voted(self, voter_id: str) -> bool:
        """Check if a voter has already voted"""
        # Check pending transactions
        for tx in self.pending_transactions:
            if tx.voter_id == voter_id:
                return True
        
        # Check blockchain
        for block in self.chain[1:]:  # Skip genesis block
            for tx in block.transactions:
                if tx.voter_id == voter_id:
                    return True
        
        return False
    
    def get_vote_count(self, jurusan: str) -> Dict[str, int]:
        """Get vote count by department"""
        vote_count = {}
        
        for block in self.chain[1:]:  # Skip genesis block
            for transaction in block.transactions:
                if transaction.jurusan == jurusan:
                    candidate = transaction.candidate
                    vote_count[candidate] = vote_count.get(candidate, 0) + 1
        
        return vote_count
    
    def get_total_votes(self) -> int:
        """Get total number of votes"""
        total = 0
        for block in self.chain[1:]:
            total += len(block.transactions)
        return total
    
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        # Validate genesis block
        if len(self.chain) > 0:
            genesis = self.chain[0]
            if genesis.index != 0 or genesis.previous_hash != "0" or len(genesis.transactions) != 0:
                return False
        
        # Validate each block
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            # Verify current block hash
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Invalid hash for block #{current_block.index}")
                return False
            
            # Verify all transactions in block
            for tx in current_block.transactions:
                if tx.hash != tx.calculate_hash():
                    print(f"❌ Invalid transaction hash in block #{current_block.index}")
                    return False
            
            # Verify link to previous block
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Block #{current_block.index} has invalid previous hash")
                return False
        
        return True

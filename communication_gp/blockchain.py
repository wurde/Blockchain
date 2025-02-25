#
# Dependencies
#

import sys
import json
import hashlib
import requests
from time import time
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse

#
# Define data structure
#

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()

        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Create the genesis block

        These are hardcoded into _most_ if not all blockchain protocols
        """

        block = {
            'index': 1,
            'timestamp': 1,
            'transactions': [],
            'proof': 1,
            'previous_hash': 1,
        }

        self.chain.append(block)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: <str> Address of the Recipient
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the BLock that will hold this transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })

        return self.last_block['index'] + 1

    def register_node(self, node):
        parsed_url = urlparse(node)
        self.nodes.add(parsed_url.netloc)

    def verify_node(self, node):
        parsed_url = urlparse(node)
        return parsed_url.netloc in self.nodes

    def broadcast_new_block(self, block):
        """
        Alert neighbors that a new block has been mined and they should add it to their chain
        as well
        """

        neighbors = self.nodes

        post_data = {"block": block}

        for node in neighbors:
            print(f"BROADCAST {node} POST /block/new {post_data}")
            response = requests.post(f'http://{node}/block/new', json=post_data)

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block": <dict> Block
        "return": <str>
        """

        # json.dumps converts json into a string
        # hashlib.sha246 is used to createa hash
        # It requires a `bytes-like` object, which is what
        # .encode() does.  It convertes the string to bytes.
        # We must make sure that the Dictionary is Ordered,
        # or we'll have inconsistent hashes

        block_string = json.dumps(block, sort_keys=True).encode()

        # By itself, this function returns the hash in a raw string
        # that will likely include escaped characters.
        # This can be hard to read, but .hexdigest() converts the
        # hash to a string using hexadecimal characters, which is
        # easer to work with and understand.  
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 6
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """

        guess = f'{block_string}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        # if guess_hash[:3] == "000":
        #     print(f"guess: {guess}, guess_hash {guess_hash} | {guess_hash[:3]} == '000' #=> {guess_hash[:3] == '000'}")

        # return guess_hash[:6] == "000000"
        return guess_hash[:3] == "000"

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid.  We'll need this
        later when we are a part of a network.

        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """

        prev_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{prev_block}')
            print(f'{block}')
            print("\n-------------------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(prev_block):
                print(f"Invalid previous hash on block {current_index}")
                return False

            # Check that the Proof of Work is correct
            block_string = json.dumps(prev_block, sort_keys=True).encode()
            if not self.valid_proof(block_string, block['proof']):
                print(f"Found invalid proof on block {current_index}")
                return False

            prev_block = block
            current_index += 1

        return True

#
# Define a web API using Flask.
#

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['POST'])
def mine():
    values = request.json

    if 'proof' in values:
        proof = values['proof']

        # Validate or reject proof of work.
        block_string = json.dumps(blockchain.last_block, sort_keys=True).encode()
        is_valid = blockchain.valid_proof(block_string, proof)
    else:
        proof = None

    if proof and is_valid:
        # We must receive a reward for finding the proof.
        # The sender is "0" to signify that this node has mined a new coin
        # The recipient is the current node, it did the mining!
        # The amount is 1 coin as a reward for mining the next block
        blockchain.new_transaction(
            sender="0",
            recipient=node_identifier,
            amount=1,
        )

        # Forge the new Block by adding it to the chain
        previous_hash = blockchain.hash(blockchain.last_block)
        block = blockchain.new_block(proof, previous_hash)

        blockchain.broadcast_new_block(block)

        # Send a response with reward
        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200
    else:
        # Send a response with rejection
        response = {
            'message': "New proof rejected"
        }
        return jsonify(response), 400


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    if values is None:
        return 'Missing Values', 400

    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing Values', 400

    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'],
                                       values['recipient'],
                                       values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/valid-chain', methods=['GET'])
def validate_chain():
    result = blockchain.valid_chain(blockchain.chain)

    response = {
        'validity': result
    }
    return jsonify(response), 200


@app.route('/last-block', methods=['GET'])
def last_block():
    result = blockchain.last_block

    response = {
        'last-block': result
    }
    return jsonify(response), 200


@app.route('/block/new', methods=['POST'])
def new_block():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required_block = ['block', 'node']
    if not all(k in values for k in required_block):
        return 'Missing Values', 400

    node = values['node']

    # Verify that the sender is one of our peers
    if blockchain.verify_node(node) is False:
        return 'Unregistered Node', 400

    new_block = values['block']

    required_values = ['index', 'previous_hash']
    if not all(k in new_block for k in required_values):
        return 'Missing Values', 400

    old_block = blockchain.last_block
    # Check that the new block index is 1 higher than our last block
    if new_block['index'] == old_block['index'] + 1:
        # Index is correct.
        if new_block['previous_hash'] == blockchain.hash(old_block):
            # Hash is correct.
            block_string = json.dumps(old_block, sort_keys=True).encode()
            if blockchain.valid_proof(block_string, new_block['proof']):
                # Proof is correct.
                blockchain.add_block(new_block)
                return 'Block Accepted', 200
        return 'Block Rejected', 400
    # Otherwise, check for consensus
    else:
        # Their index is one greater.  Block could be invalid or we could be behind.
        if new_block['index'] >= old_block['index'] + 1:
            # Do the consensus process:
            # Poll all of the nodes in our chain, and get the biggest one:
            current_chain = blockchain.chain
            for chain_node in blockchain.nodes:
                # Get the node's chain
                res = requests.get(node + '/chain')
                res = json.loads(res.content)
                if 'chain' in res and 'length' in res:
                    block_string = json.dumps(old_block, sort_keys=True).encode()
                    isvalid = blockchain.valid_proof(block_string, res['chain'])
                    if isvalid and res['length'] > len(current_chain):
                        current_chain = res['chain']
            blockchain.chain = current_chain
            return 'Consensus Performed', 200
        else:
            return 'Block Rejected', 400


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')

    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201


if __name__ == '__main__':
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 5000
    app.run(host='0.0.0.0', port=port)

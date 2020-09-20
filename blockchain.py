import hashlib
import json
from textwrap import dedent
from flask import Flask, jsonify, request
from urllib.parse import urlparse

from time import time
from uuid import uuid4

#Conflict rule: longest valid chain is authoritative. This allows us to easily resolve
#the conflict when two chains are different
class Blockchain(object):

    def __init__(self):
        self.chain=[]
        self.current_transactions = []
        self.nodes = set()
        #Create genesis block
        self.new_block(previous_hash=1, proof=100)


    def register_node(self, address):
        #Add new node to list of nodes
        #<str> address is address of node ex:'192.168.0.5:5000'
        #no return
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def valid_chain(self, chain):
        #determine validity of blockchain
        #<list> chain is a blockchain
        #<bool> returns true if valid, false otherwise
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n------------\n")

            #Check validity of block hash
            if block['previous_hash'] != self.hash(last_block):
                return False

            #Check POW
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True


    def resolve_conflicts(self):
        #Consensus algorithm, resolves conflicts by replacing our chain with the
        #longest on in the network
        #<bool> return true if chain replaces, false otherwise
        neighbors = self.nodes
        new_chain = None

        max_length = len(self.chain)

        #loop through nodes to find the longest valid chain, used as defactor blockchain
        for node in neighbors:
            response = requests.get(f'https://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json['chain']

                if length>max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False


    def proof_of_work(self, last_proof):
        #Simple POW algorithm
        #-find a number 'p' such that hash(pp') contains leading 4 zeros, where p is the previous p'
        #-p is the previous proof, and p' is the new proof
        proof = 0
        while self.valid_proof(last_proof, proof) is False:  
            proof+=1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        #Function that validates proof: Does hash(last_proof, proof) contains 4 leading 0s?
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4]=="0000"



    def new_block(self, proof, previous_hash=None):
        #Creates a new block in the chain
        #<int> proof: the proof given by Proof of Work alg
        #<str> previous_hash: optional hash of previous block
        #<dict> returns new block
        block = {
            'index': len(self.chain)+1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        #Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block



    def new_transaction(self, sender, recipient, amount):
        #Creates a new transaction to go into the next mined block
        #Returns the index of the int index of the block that will hold this transaction
        self.current_transactions.append({
            'sender':sender,
            'recipient':recipient,
            'amount':amount
        })

        return self.last_block()['index']+1



    @staticmethod
    def hash(block):
        #Uses SHA-256 hash of block
        #<str> returns hash

        #block dictionary must be ordered for consistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()


    def last_block(self):   
        return self.chain[-1]


#Using Flask microframework to map endpoints to python functions so we can communicate with blockchain using HTTP request
#/transactions/new to create new transactin to a block]
#/mine to seell server to mine a new block
#/chain to return full blockchain
#/nodes/register to add nodes
#/nodes/resolve to resolve conflicts

#Instantiate Flask Server Node
app = Flask(__name__)

#Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-','')

#Instantiate Blockchain obj
blockchain = Blockchain()


#/mine Endpoint has to: calculate POW, reward by adding new transaction of 1 coin, forge and add new block
@app.route('/mine', methods=['GET'])
def mine():
    #Run POW algorithm to get the next proof
    last_block = blockchain.last_block()
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    #reward for finding proof, send=0 means that this node has mined a coin
    blockchain.new_transaction( sender="0", recipient = node_identifier, amount = 1)

    #Forge and add new block
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactins': block['transactions'],
        'proof':block['proof'],
        'previous_hash': block['previous_hash']
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    #check that all required fields are in POST data
    required = ['sender', 'recipient', 'amount']
    # if not all (k in values for k in required):
    #     return 'Missing values', 400
    for req in required:
        check = req in values
        if check is False:
            return 'Missing values', 400

    #Create a new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message':f'Transaction will be added to Block {index}'}
    return jsonify(response, 201)


@app.route('/chain', methods=['GET'])
def full_chain():
    response= {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port = 5000)    #run on localhost port 5000


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        blockchain.register_node(node)

    response ={
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response ={
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
            
    return jsonify(response),200



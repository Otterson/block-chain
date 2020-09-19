import hashlib
import json
from textwrap import dedent
from flask import Flask, jsonify, request

from time import time
from uuid import uuid4

#https://hackernoon.com/learn-blockchains-by-building-one-117428612f46


class Blockchain(object):

    def __init__(self):
        self.chain=[]
        self.current_transactions = []

        #Create genesis block
        self.new_block(previous_hash=1, proof=100)


    def proof_of_work(self, last_proof):
        #Simple POW algorithm
        #-find a number 'p' such that hash(pp') contains leading 4 zeros, where p is the previous p'
        #-p is the previous proof, and p' is the new proof
        proof = 0
        while self.valid_proof(last_proof, proof) is False:  
            proof+=1
        return proof

    @staticmethod
    def valid_prood(last_proof, proof):
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
        self.currect_transactions.append({
            'sender':sender,
            'recipient':recipient,
            'amount':amount
        })

        return self.last_block['index']+1



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

#Instantiate Flask Server Node
app = Flask(__name__)

#Generate a globally unique address for this node
node_identifier = str(uuid4().replace('-',''))

#Instantiate Blockchain obj
blockchain = Blockchain()


#/mine Endpoint has to: calculate POW, reward by adding new transaction of 1 coin, forge and add new block
@app.route('/mine', methods['GET'])
def mine():
    #Run POW algorithm to get the next proof
    last_block = blockchain.last_block
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
    if not all (k in values for k in required):
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





#
# Dependencies
#

import hashlib
import requests
import json
import time
import sys

#
# Define method to search for proof
#

def search_for_proof(block):
    """
    Simple Proof of Work Algorithm
    Find a number p such that hash(last_block_string, p) contains 6 leading
    zeroes
    :return: A valid proof for the provided block
    """

    block_string = json.dumps(block, sort_keys=True).encode()
    
    proof = 0
    while valid_proof(block_string, proof) is False:
        proof += 1

    return proof


def valid_proof(block_string, proof):
    guess = f'{block_string}{proof}'.encode()
    guess_hash = hashlib.sha256(guess).hexdigest()

    if guess_hash[:3] == "000":
        print(f"guess: {guess}, guess_hash {guess_hash} | {guess_hash[:3]} == '000' #=> {guess_hash[:3] == '000'}")

    # return guess_hash[:6] == "000000"
    return guess_hash[:3] == "000"


#
# Execute client
#

if __name__ == '__main__':
    # What node are we interacting with?
    if len(sys.argv) > 1:
        node = sys.argv[1]
    else:
        node = "http://localhost:5000"

    coins_mined = 0
    print("Mining has started.")
    t1_start = time.process_time()
    try:
        while True:
            # Get the last proof from the server and look for a new one.
            res = requests.get(node + '/last-block')
            res = json.loads(res.content)

            # We run the proof of work algorithm to get the next proof...
            proof = search_for_proof(res['last-block'])

            # When found, POST it to the server.
            print(f"proof {proof}")
            res = requests.post(node + '/mine', json={ "proof": proof })
            res_content = json.loads(res.content)

            # If the server responds with 'New Block Forged'.
            if res.status_code == 200 and res_content['message'] == 'New Block Forged':
                coins_mined += 1
                print(f"Total Coins Mined: {coins_mined}")
            else:
                print(res_content['message'])
    except Exception as e:
        print("Mining has ended.", e)
        t1_stop = time.process_time()
        print("Elapsed time: %.1f seconds" % ((t1_stop-t1_start)))

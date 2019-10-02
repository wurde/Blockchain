#
# Dependencies
#

import hashlib
import requests
import json
import sys

#
# Define method to search for proof
#

def search_for_proof():
    """
    Simple Proof of Work Algorithm
    Find a number p such that hash(last_block_string, p) contains 6 leading
    zeroes
    :return: A valid proof for the provided block
    """
    
    proof = 0

    # TODO: Implement functionality to search for a proof 
    # TODO: Get the last proof from the server and look for a new one

    # block_string = json.dumps(block, sort_keys=True).encode()
    # while self.valid_proof(block_string, proof) is False:
    #     proof += 1

    return proof

#
# Execute client
#

if __name__ == '__main__':
    # What node are we interacting with?
    if len(sys.argv) > 1:
        node = sys.argv[1]
    else:
        node = "http://localhost:5000"

    res = requests.get(node + '/last-block')
    res = json.loads(res.content)

    last_block = res['last-block']

    # TODO: (stretch) Add a timer
    coins_mined = 0
    print("Mining has started.")
    try:
        while True:
            new_proof = search_for_proof()

            # # When found, POST it to the server.
            # res = requests.post(node + '/mine', { "proof": new_proof })
            # res_content = json.loads(res.content)

            # # If the server responds with 'New Block Forged'.
            # if res.status_code == 200:
            #     coins_mined += 1
            #     print(f"Total Coins Mined: {coins_mined}")
            # else:
            #     print(res_content['message'])
    except:
        print("Mining has ended.")

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
    # TODO: Implement functionality to search for a proof 
    return 0

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

    coins_mined = 0
    # Run forever until interrupted
    while True:
        # TODO: Get the last proof from the server and look for a new one
        # TODO: When found, POST it to the server {"proof": new_proof}
        # TODO: We're going to have to research how to do a POST in Python
        # HINT: Research `requests` and remember we're sending our data as JSON
        # TODO: If the server responds with 'New Block Forged'
        # add 1 to the number of coins mined and print it.  Otherwise,
        # print the message from the server.
        pass

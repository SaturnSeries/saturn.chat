import requests
import os
from dotenv import load_dotenv

load_dotenv()

class Activity:
    def __init__(self, description, execute):
        self.description = description
        self.execute = execute  # This is a function that performs the activity
        self.interact = execute  

    def perform_activity(self):
        """Perform the activity and return the result of the execution."""
        return self.execute()

class POAPActivity(Activity):
    def __init__(self, description):
        super().__init__(description, self.claim_poap)
        self.api_key = os.getenv("POAP_API_KEY")
        self.secret = None
        self.qr_hash = None  # Will be dynamically loaded

    def claim_poap(self):
        # Dynamically load the QR hash here (could be from a secure API or encrypted storage)
        self.qr_hash = self.fetch_dynamic_qr_hash()
        print(f"QR Hash: {self.qr_hash}")
        self.secret = self.fetch_poap_secret(self.qr_hash)
        print(f"Secret: {self.secret}")

        if self.qr_hash and self.secret:
            return self.post_claim_request()
        else:
            return "Failed to load necessary claim details."

    def fetch_dynamic_qr_hash(self):
        """
        Fetch the QR hash required to claim the POAP using the poap/links.txt file.
        It deletes the link from the file after a successful claim.
        """ 
        with open("/Users/cassini/pycode/saturn.chat/poap/links.txt", "r") as f:
            lines = f.readlines()
        if lines:
            qr_hash = lines[0].strip()
            with open("poap/links.txt", "w") as f:
                f.writelines(lines[1:])
            return qr_hash

    def fetch_poap_secret(self, qr_hash):
        """Fetch the secret required to claim the POAP using the POAP API."""
        url = f"https://api.poap.tech/actions/claim-qr?qr_hash={qr_hash}"
        headers = {"accept": "application/json", "x-api-key": self.api_key}
        print(url)
        print(headers)
        response = requests.get(url, headers=headers)
        print(response.text)
        if response.status_code == 200 and 'secret' in response.json():
            return response.json()['secret']
        else:
            return None

    def post_claim_request(self):
        """Post a claim request to the POAP API using the fetched secret."""
        url = "https://api.poap.tech/actions/claim-qr"
        payload = {
            "sendEmail": True,
            "address": os.getenv("ETH_WALLET_ADDRESS"),
            "qr_hash": self.qr_hash,
            "secret": self.secret
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        response = requests.post(url, json=payload, headers=headers)
        print(response.text)
        return "POAP claimed successfully!" if response.status_code == 200 else f"Failed to claim POAP {response.text}"

# Example of setting up activities
def setup_activities(maze_grid, start_point):
    # Example activity setup
    mining_activity = POAPActivity("Mine for rare crystals")
    # Place the activity in the starting location
    maze_grid[start_point[0]][start_point[1]].place_activity(mining_activity)

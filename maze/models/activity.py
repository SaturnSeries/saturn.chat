import requests
import os
import logging
from dotenv import load_dotenv

# Initialize environment variables and logging
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Activity:
    def __init__(self, description, execute):
        self.description = description
        self.execute = execute  # Function to perform activity
        self.interact = execute  

    def perform_activity(self):
        """ Wrapper to execute the activity function. """
        return self.execute()

class POAPActivity(Activity):
    def __init__(self, description, links_file="links.txt"):
        super().__init__(description, self.claim_poap)
        self.api_key = os.getenv("POAP_API_KEY")
        self.wallet_address = os.getenv("ETH_WALLET_ADDRESS")
        self.links_file = links_file
        self.secret = None
        self.qr_hash = None
        self.access_token = None


    def get_auth_token(self):
        """Fetch the auth token using client credentials."""
        url = 'https://auth.accounts.poap.xyz/oauth/token'
        headers = {"Content-Type": "application/json"}
        payload = {
            "audience": "https://api.poap.tech",
            "grant_type": "client_credentials",
            "client_id": os.getenv("POAP_CLIENT_ID"),
            "client_secret": os.getenv("POAP_CLIENT_SECRET")
        }
        response = requests.post(url, json=payload, headers=headers)
        logging.debug(f"Token request payload: {payload}")
        if response.status_code == 200:
            logging.info("Auth token fetched successfully.")
            return response.json().get('access_token')
        else:
            logging.error(f"Failed to fetch auth token: {response.text}")
            return None

    def fetch_poap_claim_qr(self, access_token, qr_hash):
        """Fetch POAP claim using the provided access token and qr_hash."""
        url = f"https://api.poap.tech/actions/claim-qr?qr_hash={qr_hash}"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {access_token}",
            "x-api-key": os.getenv("POAP_API_KEY")
        }
        response = requests.get(url, headers=headers)
        logging.debug(f"Fetching POAP with QR hash: {qr_hash}")
        if response.status_code == 200:
            logging.info("POAP claim data fetched successfully.")
            return response.json()
        else:
            logging.error(f"Failed to fetch POAP claim: {response.text}")
            return None

    def finalize_poap_claim(self, qr_hash, secret, access_token):
        """Send request to finalize POAP claim."""
        url = "https://api.poap.tech/actions/claim-qr"
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {access_token}",
            "x-api-key": os.getenv("POAP_API_KEY")
        }
        payload = {
            "sendEmail": True,
            "address": os.getenv("ETH_WALLET_ADDRESS"),
            "qr_hash": qr_hash,
            "secret": secret
        }
        response = requests.post(url, json=payload, headers=headers)
        logging.debug(f"Finalizing POAP claim with payload: {payload}")
        if response.status_code == 200:
            logging.info("POAP claimed successfully!")
            return response.json()
        else:
            logging.error(f"Failed to claim POAP: {response.text}")
            return None

    def fetch_dynamic_qr_hash(self):
        """Fetch and remove the first QR hash from the local file."""
        logging.info("Fetching dynamic QR hash.")
        try:
            with open("links.txt", "r") as f:
                lines = f.readlines()
            if not lines:
                logging.warning("No QR hashes found in the file.")
                return None
            url = lines[0].strip()
            qr_hash = url.split("/")[-1]
            with open("links.txt", "w") as f:
                f.writelines(lines[1:])
            logging.debug(f"Dynamic QR hash fetched: {qr_hash}")
            return qr_hash
        except FileNotFoundError:
            logging.error("QR hash file not found.")
            return None
        except Exception as e:
            logging.error(f"Error reading QR hash: {str(e)}")
            return None
        
    def claim_poap(self):
        access_token = self.get_auth_token()
        if access_token:
            qr_hash = self.fetch_dynamic_qr_hash()
            if qr_hash:
                claim_data = self.fetch_poap_claim_qr(access_token, qr_hash)
                if claim_data and 'secret' in claim_data:
                    final_result = self.finalize_poap_claim(qr_hash, claim_data['secret'], access_token)
                    logging.info(f"Final Claim Result: {final_result}")
                    return final_result
                else:
                    logging.error("No secret found to finalize claim.")
                    return "No secret found to finalize claim."
            else:
                logging.error("Failed to fetch a valid QR hash.")
                return "Failed to fetch a valid QR hash."
        else:
            logging.error("No access token obtained.")
            return "No access token obtained."
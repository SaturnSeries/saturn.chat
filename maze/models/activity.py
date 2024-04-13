#########################
# Custom Activity Class #
#########################

class Activity:
    def __init__(self, description, execute):
        self.description = description
        self.execute = execute  # This is a function that performs the activity
        self.interact = execute  
    def perform_activity(self):
        """Perform the activity and return the result of the execution."""
        return self.execute()


class POAPActivity(Activity):
    def __init__(self, description, qr_hash, fetch_secret_func):
        super().__init__(description, self.claim_poap)
        self.qr_hash = qr_hash
        self.fetch_secret_func = fetch_secret_func
        self.api_key = config.poap_api_key
        self.secret = None

    def claim_poap(self):
        if not self.secret:
            self.secret = self.fetch_secret_func()
        url = "https://api.poap.tech/actions/claim-qr"
        payload = {
            "sendEmail": False,
            "address": config.eth_address,
            "qr_hash": self.qr_hash,
            "secret": self.secret
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "x-api-key": self.api_key
        }
        response = requests.post(url, json=payload, headers=headers)
        return "POAP claimed successfully!" if response.status_code == 200 else f"Failed to claim POAP {response.text}"

    def fetch_poap(self):
        url = "https://api.poap.tech/actions/claim-qr"
        headers = {"accept": "application/json", "x-api-key": self.api_key}
        response = requests.get(url, headers=headers)
        return response.json() if response.status_code == 200 else "Failed to fetch POAP data"



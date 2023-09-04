from datetime import datetime
import os
import logging
from threading import Thread
import time
from typing import Optional
import requests
import pickle


os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/cloudflare_rdns.log"), logging.StreamHandler()],
)


WAIT_TIME = 300  # seconds, 5 minutes


class App(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.data_dir = "data"
        self.data_last_5_ips = f"{self.data_dir}/last_5_ips.pickle"
        self.stopped = False

        self.__cf_api_token = os.environ.get("CF_API_TOKEN")
        self.__cf_account_id = os.environ.get("CF_ACCOUNT_ID")
        self.__cf_zone_id = os.environ.get("CF_ZONE_ID")
        self.__cf_record_name = os.environ.get("CF_RECORD_NAME")

        self.setup()

    def setup(self):
        logging.info("Setting up...")

        logging.info("Creating directories...")
        for dir in [self.data_dir]:
            if not os.path.exists(dir):
                logging.info(f"Creating directory: {dir}")
                os.makedirs(dir)

    def run(self):
        logging.info("Running...")
        while not self.stopped:
            ip = self.get_public_ip()
            if not ip:
                continue

            logging.info(f"Public IP changed to: {ip}")
            logging.info("Searching for zone record...")
            zone_record = self.cf_get_zone()

            response = None
            if not zone_record:
                logging.info("Creating zone record...")
                response = self.cf_dns_create_record(ip)
            else:
                logging.info("Updating zone record...")
                response = self.cf_dns_update_record(zone_record["id"], ip)

            if not response:
                logging.error("No response from Cloudflare")
            elif response["success"] == False:
                logging.error(f"Error from Cloudflare: {response['errors']}")
            else:
                logging.info(f'Record updated successfully: {response["result"]}')

            time.sleep(WAIT_TIME)

    def cf_get_zone(self):
        # curl --request GET --url "https://api.cloudflare.com/client/v4/zones/ZONID/dns_records" -H "Authorization: Bearer AUTHKET" -H "Content-Type:application/json"
        url = f"https://api.cloudflare.com/client/v4/zones/{self.__cf_zone_id}/dns_records"
        request = requests.get(
            url=url,
            headers={
                "Authorization": f"Bearer {self.__cf_api_token}",
                "Content-Type": "application/json",
            },
            params={"name": self.__cf_record_name},
        )

        records = request.json().get("result", [])
        if not records or len(records) <= 0:
            return None
        else:
            return records[0]

    def cf_dns_create_record(self, ip: Optional[str]):
        if not ip:
            return None

        url = f"https://api.cloudflare.com/client/v4/zones/{self.__cf_zone_id}/dns_records"
        request = requests.post(
            url=url,
            headers={
                "Authorization": f"Bearer {self.__cf_api_token}",
                "Content-Type": "application/json",
            },
            json={
                "content": self.get_public_ip(),
                "name": self.__cf_record_name,
                "proxied": False,
                "type": "A",
                "comment": f"cloudflare_rdns.py, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                # "tags": ["cloudflare_rdns.py"],
                "ttl": 1,
            },
        )

        return request.json()

    def cf_dns_update_record(self, identifier: str, ip: Optional[str]):
        if not ip:
            return None

        url = f"https://api.cloudflare.com/client/v4/zones/{self.__cf_zone_id}/dns_records/{identifier}"
        request = requests.put(
            url=url,
            headers={
                "Authorization": f"Bearer {self.__cf_api_token}",
                "Content-Type": "application/json",
            },
            json={
                "content": self.get_public_ip(),
                "name": self.__cf_record_name,
                "proxied": False,
                "type": "A",
                "comment": f"cloudflare_rdns.py, {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                # "tags": ["cloudflare_rdns.py"],
                "ttl": 1,
            },
        )

        return request.json()

    def get_public_ip(self):
        request = requests.get("https://api.ipify.org/")
        return request.text.strip() if request.status_code == 200 else None

    def get_public_ip_if_changed(self):
        if os.path.exists(self.data_last_5_ips):
            logging.debug("Loading last 5 IPs from file...")
            with open(self.data_last_5_ips, "rb") as f:
                last_5_ips = pickle.load(f)
        else:
            last_5_ips = []

        ip = self.get_public_ip()
        if not ip:
            logging.warning("Could not get public IP. Skipping...")
            return None

        last_5_ips.append(ip)
        last_5_ips = last_5_ips[-5:] if len(last_5_ips) > 5 else last_5_ips

        with open(self.data_last_5_ips, "wb") as f:
            logging.debug("Saving last 5 IPs to file...")
            pickle.dump(last_5_ips, f)

        return ip if len(last_5_ips) <= 1 or last_5_ips[-1] != last_5_ips[-2] else None


if __name__ == "__main__":
    app = App()

    try:
        logging.info("Starting...")
        app.start()
        app.join()
    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt. Stopping...")
        app.stopped = True

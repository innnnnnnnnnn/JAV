import requests
import base64
import logging
import xml.etree.ElementTree as ET
import json

logger = logging.getLogger(__name__)

class QnapDownloadStation:
    def __init__(self, host, username, password, download_path="MYBOOK"):
        self.host = host.rstrip('/')
        self.username = username
        self.password = password
        self.download_path = download_path.strip('/') # Support both "MYBOOK" and "/MYBOOK"
        self.sid = None
        self.session = requests.Session()

    def login(self):
        """
        Authenticates with QNAP and gets a session ID (authSid).
        """
        logger.info(f"Attempting login to QNAP at {self.host}")
        url = f"{self.host}/cgi-bin/authLogin.cgi"

        # QNAP requires base64-encoded password
        pw_b64 = base64.b64encode(self.password.encode()).decode()
        params = {"user": self.username, "pwd": pw_b64}

        try:
            response = self.session.get(url, params=params, timeout=10)
            logger.debug(f"Login response: {response.text}")

            root = ET.fromstring(response.text)
            auth_passed = root.findtext('authPassed')
            if auth_passed != '1':
                logger.error(f"QNAP authPassed={auth_passed}. Login denied.")
                return False

            self.sid = root.findtext('authSid')
            if not self.sid:
                logger.error("Login OK but authSid not found in response.")
                return False

            # Set cookie for subsequent requests
            self.session.cookies.set('NAS_SID', self.sid)
            logger.info(f"Successfully logged in to QNAP. SID: {self.sid}")
            return True

        except Exception as e:
            logger.error(f"QNAP Login exception: {e}")

        return False

    def add_task(self, torrent_url):
        """
        Adds a torrent URL to Download Station using the V4 API.
        """
        if not self.sid:
            if not self.login():
                return False

        # Endpoint found via browser inspection
        url = f"{self.host}/downloadstation/V4/Task/AddUrl"
        
        # In QTS 5.x Download Station 5, the following parameters are used:
        # url: The torrent/magnet link. (Sending as plain string seems more compatible than JSON list in form data)
        # temp: The target share name (e.g. MYBOOK)
        # move: The target share name (e.g. MYBOOK)
        # sid: The session ID
        data = {
            "temp": self.download_path,
            "move": self.download_path,
            "url": torrent_url,
            "sid": self.sid
        }

        # Essential headers for DS 5 API
        headers = {
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{self.host}/downloadstation/",
            "Origin": self.host
        }

        try:
            # We use data=... for application/x-www-form-urlencoded
            response = self.session.post(url, data=data, headers=headers, timeout=15)
            logger.info(f"Add task response: {response.text}")

            # Session expired?
            if '"error":5' in response.text or "session error" in response.text.lower():
                logger.warning("Session expired or invalid, re-logging...")
                if self.login():
                    data["sid"] = self.sid
                    response = self.session.post(url, data=data, headers=headers, timeout=15)
                else:
                    return False

            # Parse success
            res_json = response.json()
            if res_json.get('error') == 0:
                logger.info("Task successfully added to QNAP.")
                return True
            else:
                # 8196 = task already exists, 4096 = path error?
                if res_json.get('error') == 8196:
                    logger.info("Task already exists in QNAP.")
                    return True
                logger.error(f"QNAP returned error: {res_json}")

        except Exception as e:
            logger.error(f"Exception while adding task to QNAP: {e}")

        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Support manual testing
    # python3 qnap_api.py - test adding a known torrent

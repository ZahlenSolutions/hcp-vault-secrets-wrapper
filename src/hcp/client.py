# hcp_vault_secrets_wrapper/client.py

import http.client
from http.client import HTTPException
import urllib.parse
import json
from datetime import datetime,timedelta
import os

HCP_REFRESH_DEFAULT = 25
HCP_REFRESH_TIMEOUT_MIN = os.environ.get("HCP_REFRESH_TIMEOUT_MIN") or HCP_REFRESH_DEFAULT
try:
    HCP_REFRESH_TIMEOUT_MIN = int(HCP_REFRESH_TIMEOUT_MIN)
except Exception:
    HCP_REFRESH_TIMEOUT_MIN = HCP_REFRESH_DEFAULT
    

HCP_DEFAULT_SECRET_URI = "/secrets/2023-11-28/organizations/{org_id}/projects/{project_id}/apps/{app_id}/secrets:open"

class HCPVaultClient:
    last_refresh:datetime = None
    last_secrets:any = None
    def __init__(self, client_id:str, client_secret:str, org_id:str, project_id:str, app_id:str, secret_uri:str=HCP_DEFAULT_SECRET_URI, refresh_timeout_min:int=HCP_REFRESH_TIMEOUT_MIN, clear_refresh:bool=False):
        if clear_refresh:
            HCPVaultClient.last_refresh = None
        self.refresh_timeout = refresh_timeout_min
        self.client_id = client_id
        self.client_secret = client_secret
        self.org_id = org_id
        self.project_id = project_id        
        self.app_id = app_id        
        self.secret_uri = secret_uri
        self.token = None

    def _get_oauth_token(self):
        """
        Private method to obtain an OAuth token using client credentials.
        """
        # Define request parameters
        data = urllib.parse.urlencode({
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "audience": "https://api.hashicorp.cloud",
        })
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Perform the request
        try:
            conn = http.client.HTTPSConnection("auth.idp.hashicorp.com")
            conn.request("POST", "/oauth2/token", body=data, headers=headers)
            response = conn.getresponse()
            response_data = response.read()
            conn.close()
        except Exception as x:
            raise HTTPException(f"Issue during OAUTH connection: {x}")
        # Parse and return token
        token_data = json.loads(response_data.decode("utf-8"))
        return token_data.get("access_token")

    def fetch_secrets(self):
        """
        Fetch secrets from the HCP Vault using the stored OAuth token.
        """
        if not self.org_id:
            raise ValueError("HCP Org ID not supplied.  Cannot make call")
        if not self.project_id:
            raise ValueError("HCP Project ID not supplied.  Cannot make call")
        if not self.app_id:
            raise ValueError("HCP App ID not supplied.  Cannot make call")

        refresh_due = HCPVaultClient.last_refresh == None or \
            (datetime.now() - HCPVaultClient.last_refresh) > timedelta(minutes=self.refresh_timeout)
        if refresh_due:
            self.token = self._get_oauth_token()

            # Define request headers
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            try:
                # Define API endpoint (customize organization, project, app)
                conn = http.client.HTTPSConnection("api.cloud.hashicorp.com")
                conn.request("GET", self.secret_uri.format(org_id=self.org_id, project_id=self.project_id, app_id=self.app_id), headers=headers)
                response = conn.getresponse()
                response_data = response.read()
                conn.close()
                # Parse and return the secret data
                HCPVaultClient.last_secrets = json.loads(response_data.decode("utf-8"))        
                HCPVaultClient.last_refresh = datetime.now()
            except Exception as x:
                raise HTTPException(f"Issue during secrets fetch connection: {x}")
        return self._process_secrets()

    def _process_secrets(self):
        final_data = {}
        last_secrets = HCPVaultClient.last_secrets
        if "secrets" in last_secrets:
            for secret in last_secrets["secrets"]:
                if secret['type'] == 'kv':
                    final_data[secret["name"]] = secret["static_version"]["value"]
                if secret['type'] == 'dynamic':
                    final_data[secret["name"]] = secret["dynamic_instance"]
        return final_data
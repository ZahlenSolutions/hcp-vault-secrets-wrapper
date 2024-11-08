# hcp_vault_secrets_wrapper/client.py

import http.client
from http.client import HTTPException
import urllib.parse
import json

HCP_DEFAULT_SECRET_URI = "/secrets/2023-11-28/organizations/{org_id}/projects/{project_id}/apps/{app_id}/secrets:open"

class HCPVaultClient:
    def __init__(self, client_id:str, client_secret:str, org_id:str, project_id:str, app_id:str, secret_uri:str=HCP_DEFAULT_SECRET_URI ):
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

        if not self.token:
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
        except Exception as x:
            raise HTTPException(f"Issue during secrets fetch connection: {x}")
        # Parse and return the secret data
        self.last_secrets = json.loads(response_data.decode("utf-8"))        
        return self._process_secrets()

    def _process_secrets(self):
        final_data = {}
        if "secrets" in self.last_secrets:
            for secret in self.last_secrets["secrets"]:
                if secret['type'] == 'kv':
                    final_data[secret["name"]] = secret["static_version"]["value"]
                if secret['type'] == 'dynamic':
                    final_data[secret["name"]] = secret["dynamic_instance"]
        return final_data
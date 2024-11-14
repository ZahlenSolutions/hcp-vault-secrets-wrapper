# hcp-vault-secrets-wrapper
Simple HCP Vault Secrets Wrapper library

## Approach
- Simple HTTP client implementation in generic python

## Required Variables
- **Client ID** and **Client Secret**: each application requires a unique client ID and secret.  Keep these values secret.
- Client Org, App and Project IDs, which can be fetched from the secrets fetching URL provided by HCP:
  - Example:
`https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/XXXX/projects/YYYY/apps/ZZZZ/secrets:open`
    - XXXX is the organization ID (a UUID)
    - YYYY is the project ID (also a UUID)
    - ZZZZ is the application ID (should be human-readble)

## Implementation
- Use the following pattern to setup an HCP Vault connection for an application

```python
# Keep Secret
HCP_CLIENT_ID = getenv("HCP_CLIENT_ID") or None
HCP_CLIENT_SECRET = getenv("HCP_CLIENT_SECRET") or None

# Not Secret - get from HCP Vault app screen:
HCP_ORG_ID = getenv("HCP_ORG_ID") or None
HCP_PROJECT_ID = getenv("HCP_PROJECT_ID") or None
HCP_APP_ID = getenv("HCP_APP_ID") or None

# Setup secrets manage setup
secrets_mgr = HCPVaultClient(HCP_CLIENT_ID, HCP_CLIENT_SECRET, HCP_ORG_ID, HCP_PROJECT_ID, HCP_APP_ID)
# Fetch secrets
secrets_data = secrets_mgr.fetch_secrets() # Returns object with secrets from HCP
# Access static secrets:
some_secret = secrets_data["SOME_SECRET"]
# Access dynamic secrets and set environ variable 
from os import environ
environ["AWS_ACCESS_KEY_ID"] = secrets_data["SOME_SECRET_AWS"]["values"]["access_key_id"]
environ["AWS_SECRET_ACCESS_KEY"] = secrets_data["SOME_SECRET_AWS"]["values"]["secret_access_key"]
environ["AWS_SESSION_TOKEN"] = secrets_data["SOME_SECRET_AWS"]["values"]["session_token"]
```

## Refresh secrets
- The code contains two class variables that cache the secrets to avoid over-querying of secrets from HCP.
    - By default, secrets are cached for 25 minutes (or can be controlled by the `refresh_timeout_min` constructor variable)
- Call `fetch_secrets` to either pull new secrets (if we exceed the refresh timeout) OR return the last cached secrets.

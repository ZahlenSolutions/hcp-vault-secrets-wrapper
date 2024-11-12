from datetime import datetime, timedelta
from dotenv import load_dotenv
from os.path import abspath
from os import getenv
from hcp import HCPVaultClient
import json


class TestBaselineFunctionality:
    def setup_method(self):
        ENV_FILE = abspath(getenv("ENV") or "tests/test_secrets/.env")
        load_dotenv(ENV_FILE)
        self.HCP_CLIENT_SECRETS = getenv("HCP_CLIENT_SECRETS")

        self.HCP_ORG_ID = getenv("HCP_ORG_ID")
        self.HCP_PROJECT_ID = getenv("HCP_PROJECT_ID")
        self.HCP_APP_ID = getenv("HCP_APP_ID")
        self.HCP_CLIENT_ID = json.loads(self.HCP_CLIENT_SECRETS)["HCP_CLIENT_ID"]
        self.HCP_CLIENT_SECRET = json.loads(self.HCP_CLIENT_SECRETS)["HCP_CLIENT_SECRET"]    
    
    def teardown_method(self):
        HCPVaultClient.last_refresh = None
    
    def test_environment_complete(self):
        assert self.HCP_ORG_ID is not None
        assert self.HCP_PROJECT_ID is not None
        assert self.HCP_APP_ID is not None
        assert self.HCP_CLIENT_ID is not None
        assert self.HCP_CLIENT_SECRET is not None
    
    def test_initial_connection(self):
        assert HCPVaultClient.last_refresh is None
        test_client = HCPVaultClient(self.HCP_CLIENT_ID,self.HCP_CLIENT_SECRET,self.HCP_ORG_ID,self.HCP_PROJECT_ID,self.HCP_APP_ID)
        assert test_client.fetch_secrets() is not None
        assert HCPVaultClient.last_refresh is not None
    
    def test_last_refresh_set_correctly(self):
        assert HCPVaultClient.last_refresh is None
        test_client = HCPVaultClient(self.HCP_CLIENT_ID,self.HCP_CLIENT_SECRET,self.HCP_ORG_ID,self.HCP_PROJECT_ID,self.HCP_APP_ID)
        assert test_client.fetch_secrets() is not None
        assert HCPVaultClient.last_refresh is not None
    
    def test_last_refresh_prevents_additional_calls(self):
        assert HCPVaultClient.last_refresh is None
        test_client = HCPVaultClient(self.HCP_CLIENT_ID,self.HCP_CLIENT_SECRET,self.HCP_ORG_ID,self.HCP_PROJECT_ID,self.HCP_APP_ID)
        assert test_client.fetch_secrets() is not None
        assert HCPVaultClient.last_refresh is not None
        # save last refresh time
        last_refresh = HCPVaultClient.last_refresh
        # fetch again, should not update last refresh
        test_client.fetch_secrets()
        assert last_refresh == HCPVaultClient.last_refresh # Should not have changed, refresh time not exceeded
        
    def test_refresh_managed_between_instances(self):
        assert HCPVaultClient.last_refresh is None
        test_client = HCPVaultClient(self.HCP_CLIENT_ID,self.HCP_CLIENT_SECRET,self.HCP_ORG_ID,self.HCP_PROJECT_ID,self.HCP_APP_ID)
        assert test_client.fetch_secrets() is not None
        assert HCPVaultClient.last_refresh is not None
        # Force refresh even with a new instance
        previous_time = datetime.now() - timedelta(minutes=60)
        HCPVaultClient.last_refresh = previous_time
        test_client2 = HCPVaultClient(self.HCP_CLIENT_ID,self.HCP_CLIENT_SECRET,self.HCP_ORG_ID,self.HCP_PROJECT_ID,self.HCP_APP_ID)
        test_client2.fetch_secrets()
        assert HCPVaultClient.last_refresh is not None and HCPVaultClient.last_refresh > previous_time # Updated and in the future
                


# def test_correct_testing_env():
#     return HCPVaultClient(HCP_CLIENT_ID,HCP_CLIENT_SECRET,HCP_ORG_ID,HCP_PROJECT_ID,HCP_APP_ID)

# def test_get_secrets():    
#     client_test = test_correct_testing_env()
#     results = client_test.fetch_secrets()
#     assert results is not None
#     assert HCPVaultClient.last_refresh is not None


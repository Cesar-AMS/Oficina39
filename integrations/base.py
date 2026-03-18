class IntegrationAdapter:
    provider_name = ''
    requires_api_key = False

    def __init__(self, api_key=None):
        self.api_key = (api_key or '').strip() or None

    def headers(self):
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            headers['X-API-Key'] = self.api_key
        return headers

    def fetch(self, query):
        raise NotImplementedError

    def normalize(self, payload):
        raise NotImplementedError

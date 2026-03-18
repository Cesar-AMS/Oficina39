import json
from urllib.request import Request, urlopen


def request_json(url, headers=None, method='GET', data=None, timeout=8):
    request = Request(url, headers=headers or {}, method=method)
    if data is not None:
        payload = json.dumps(data).encode('utf-8')
        request.add_header('Content-Type', 'application/json')
    else:
        payload = None

    with urlopen(request, data=payload, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        return json.loads(response.read().decode(charset))

def post(self, url, **kwargs):
    resp = self._session.post(url, **kwargs)
    return resp.content

def get(self, url, **kwargs):
    resp = self._session.get(url, **kwargs)
    if resp.status_code == 200:
        return resp.content
    return None

def post_json(self, url, **kwargs):
    """Downloads data with the given url and converts it to json"""
    resp = self.post(url, **kwargs)
    if resp == None:
        return None
    return json.loads(resp.decode('utf8'))

def get_json(self, url, **kwargs):
    """Downloads data with the given url and converts it to json"""
    resp = self.get(url, **kwargs)
    if resp == None:
        return None
    return json.loads(resp.decode('utf8'))

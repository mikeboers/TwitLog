from urlparse import urljoin
from requests_oauthlib import OAuth1Session as _Session


base_url = 'https://api.twitter.com/1.1/'


class OathSession(_Session):

    def request(self, method, url, *args, **kwargs):
        abs_url = urljoin(base_url, url)
        if abs_url != url:
            abs_url += '.json'
        return super(OathSession, self).request(method, abs_url, *args, **kwargs)

    def get_json(self, url, **kwargs):
        return self.get(url, **kwargs).json()

    def iter_json(self, url, **kwargs):
        cursor = kwargs.pop('cursor', None)
        params = dict(kwargs.pop('params'))
        kwargs['params'] = params
        while True:
            if cursor is not None:
                params['cursor'] = str(cursor)
            res = self.get_json(url, **kwargs)
            cursor = res['next_cursor']
            yield res
            if not cursor:
                return



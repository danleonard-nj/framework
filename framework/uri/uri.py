import urllib
from urllib.parse import ParseResult, parse_qs, urlencode, urlparse
from deprecated import deprecated


@deprecated
def build_url(base, **kwargs):
    url = base
    if kwargs:
        url += '?'
    args = list(kwargs.items())
    for arg in args:
        url += str(arg[0])
        url += '='
        url += urllib.parse.quote_plus(str(arg[1]))
        if arg[0] != args[-1][0]:
            url += '&'
    return url


class Uri:
    def __init__(self, url: str = None):
        self._port = None
        self._host = None
        self._elements = self.get_default_elements()

        if url:
            self._elements = self.parse_elements(
                url=url)

    _element_keys = [
        'scheme',
        'netloc',
        'params',
        'query',
        'path',
        'fragment'
    ]

    def get_default_elements(self):
        return {
            'scheme': 'https',
            'path': '',
            'params': '',
            'query': '',
            'netloc': '',
            'fragment': ''
        }

    @property
    def host(self) -> str:
        return self.none_if_empty(
            value=self._host)

    @host.setter
    def host(self, value: dict):
        self._host = value

    @property
    def params(self):
        return self.none_if_empty(
            value=self._elements.get('params'))

    @params.setter
    def params(self, value):
        self._elements['params'] = value

    @property
    def scheme(self) -> str:
        return self.none_if_empty(
            value=self._elements.get('scheme'))

    @scheme.setter
    def scheme(self, value: str):
        self._elements['scheme'] = value

    @property
    def query(self) -> str:
        _query = self._elements.get('query')
        if not _query or _query == '':
            return None
        return parse_qs(_query)

    @query.setter
    def query(self, value: dict):
        _query = urlencode(value)
        self._elements['query'] = _query

    @property
    def port(self) -> int:
        return self._port

    @port.setter
    def port(self, value: int):
        self._port = value

    @property
    def path(self) -> int:
        return self._elements.get('path')

    @path.setter
    def path(self, value: int):
        self._elements['path'] = value

    @property
    def segments(self) -> list[str]:
        path = self.path
        segments = path.split('/')
        if any(segments):
            return segments[1:]

    @segments.setter
    def segments(self, value: list[str]):
        _segments = ['']
        _segments.extend(value)

        self._elements['path'] = '/'.join(_segments)

    def parse_netloc_str(self, netloc):
        if ':' in netloc:
            segments = netloc.split(':')
            return {
                'netloc': segments[0],
                'port': segments[1]
            }
        else:
            return {
                'netloc': netloc,
                'port': 0
            }

    def get_url_port(self, url):
        if ':' in url.netloc:
            return url.netloc.split(':')[1]
        else:
            return None

    def get_url_host(self, url):
        if ':' in url.netloc:
            return url.netloc.split(':')[0]
        else:
            return url.netloc

    def get_netloc_str(self):
        if self.port and self.port != 0:
            return f'{self.host}:{self.port}'
        else:
            return self.host

    def parse_elements(self, url: str):
        obj = urlparse(url)
        elements = dict()

        for key in self._element_keys:
            value = getattr(obj, key)
            if key == 'netloc':
                self._host = self.get_url_host(obj)
                self._port = self.get_url_port(obj)
            else:
                elements[key] = value
        return elements

    def get_url(self):
        if not self._host:
            raise Exception('no host is defined')

        self._elements['netloc'] = self.get_netloc_str()
        parsed = ParseResult(**self._elements)
        return parsed.geturl()

    def none_if_empty(self, value):
        if isinstance(value, str) and value == '':
            return None
        else:
            return value

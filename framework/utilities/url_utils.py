
import urllib


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

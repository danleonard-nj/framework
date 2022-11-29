import httpx
from deprecated import deprecated


@deprecated
class HttpClient:
    def _get_default_builder(self):
        return lambda: httpx.AsyncClient()

    async def request(self, url, method, client_builder=None, **kwargs):
        builder = client_builder or self._get_default_builder()

        async with builder() as api:
            return await api.request(
                method=method,
                url=url,
                **kwargs)

    async def post(self, url, **kwargs):
        return await self.request(
            url=url,
            method='POST',
            **kwargs)

    async def get(self, url, **kwargs):
        return await self.request(
            url=url,
            method='GET',
            **kwargs)

    async def put(self, url, **kwargs):
        return await self.request(
            url=url,
            method='PUT',
            **kwargs)

    async def delete(self, url, **kwargs):
        return await self.request(
            url=url,
            method='DELETE',
            **kwargs)

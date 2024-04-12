
class HttpException(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class RequestHeaderException(Exception):
    def __init__(self, header, *args: object) -> None:
        super().__init__(
            f"No header with the key '{header}' found in requet context")

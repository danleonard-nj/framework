
class RequestHeaderException(Exception):
    def __init__(self, header, *args: object) -> None:
        super().__init__(
            f"No header with the key '{header}' found in requet context")

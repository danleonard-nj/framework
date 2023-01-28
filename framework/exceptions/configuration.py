

class ConfigurationException(Exception):
    def __init__(self, message: str):
        self.message = message


class ConfigurationSourceException(Exception):
    def __init__(self, environemnt, *args: object) -> None:
        super().__init__(
            f"No configuration file is known for environment '{environemnt}'")

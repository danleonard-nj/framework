from deprecated import deprecated


class Serializable:
    def serializer_exclude(self):
        return list()

    def serializer_include(self):
        return list()

    @deprecated
    def _fields(self):
        return list()

    @deprecated
    def _exclude(self):
        return list()

    def to_dict(self):
        result = self.__dict__.copy()
        if any(self._fields()):
            result = {
                k: v for k, v in result.items()
                if k in self._fields()
            }

        if any(self.serializer_include()):
            result = {
                k: v for k, v in result.items()
                if k in self.serializer_include()
            }

        if any(self._exclude()):
            result = {
                k: v for k, v in result.items()
                if k not in self._exclude()
            }

        if any(self.serializer_exclude()):
            result = {
                k: v for k, v in result.items()
                if k not in self.serializer_exclude()
            }

        return result

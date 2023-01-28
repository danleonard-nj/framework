from typing import Dict


class Serializable:
    def serializer_exclude(
        self
    ):
        '''
        Optional list of attributes to
        exclude from serialization
        '''

        return list()

    def serializer_include(
        self
    ):
        '''
        Optional exclusive attribute list
        to include in serialization
        '''

        return list()

    def to_dict(
        self
    ) -> Dict:
        '''
        Serialize an object to dictionary
        '''

        result = self.__dict__.copy()

        if any(self.serializer_include()):
            result = {
                k: v for k, v in result.items()
                if k in self.serializer_include()
            }

        if any(self.serializer_exclude()):
            result = {
                k: v for k, v in result.items()
                if k not in self.serializer_exclude()
            }

        return result

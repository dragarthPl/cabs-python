class Feature:
    __enabled: bool = False
    __label: str = ""

    def __init__(self, enabled: bool, description: str):
        self.__enabled = enabled
        self.__label = description

    def is_active(self):
        return self.__enabled

    @property
    def label(self):
        return self.__label

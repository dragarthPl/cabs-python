class DocumentNumber:
    __number: str

    def __init__(self, number: str):
        self.__number = number

    @property
    def number(self):
        return self.__number

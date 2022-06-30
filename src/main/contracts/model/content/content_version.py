class ContentVersion:
    __content_version: str

    def __init__(self, content_version):
        self.__content_version = content_version

    @property
    def content_version(self):
        return self.__content_version

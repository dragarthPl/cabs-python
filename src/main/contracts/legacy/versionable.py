from abc import ABCMeta


class Versionable(metaclass=ABCMeta):
    def recreate_to(self, version: int):
        raise NotImplementedError

    def get_last_version(self) -> int:
        raise NotImplementedError

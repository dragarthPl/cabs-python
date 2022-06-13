from abc import ABCMeta

from pydantic import BaseModel


class Printable(BaseModel, metaclass=ABCMeta):
    pass

from abc import ABCMeta, abstractmethod


class OOParadigm(metaclass=ABCMeta):
    # 2. enkapsulacja - ukrycie impl
    __filed: object

    # 1. abstrakcja - agent odbierający sygnały
    def method(self):
        pass
        # do sth

    # 3. polimorfizm - zmienne zachowania
    @abstractmethod
    def _abstract_step(self):
        raise NotImplementedError


#4. dziedziczenie - technika wspierająca polimorizm
class ConcreteType(OOParadigm):

    def _abstract_step(self):
        pass

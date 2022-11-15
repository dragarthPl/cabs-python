from injector import inject
from mockito import when

from money import Money
from pricing.tariff import Tariff
from pricing.tariffs import Tariffs
from ride.transit import Transit


class StubbedTransitPrice:
    tariffs: Tariffs

    @inject
    def __init__(self, tariffs: Tariffs):
        self.tariffs = tariffs

    def stub(self, faked: Money) -> Transit:
        fake_tariff: Tariff = Tariff(0, "fake", faked)
        # when(self.tariffs).choose(isA(Instant.class)).thenReturn(fake_tariff)


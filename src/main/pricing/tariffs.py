from datetime import datetime

from dateutil.tz import tzlocal

from pricing.tariff import Tariff


class Tariffs:

    def choose(self, when: datetime) -> Tariff:
        if not when:
            when = datetime.now()
        return Tariff.of_time(when.astimezone(tzlocal()))

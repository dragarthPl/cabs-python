from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import Any


class EventObject:
    _source: Any

    def __init__(self, source: Any):
        if source is None:
            raise AttributeError("null source")

        self._source = source

    @property
    def source(self):
        return self._source

    def to_string(self):
        return f"{str(self.__class__.__name__)}[source={self._source}]"

    def __str__(self):
        return self.to_string()


class ApplicationEvent(EventObject, metaclass=ABCMeta):
    __timestamp: int

    def __init__(self, source: Any):
        super().__init__(source)
        self.__timestamp = round(datetime.now().timestamp())

    @property
    def timestamp(self):
        return self.__timestamp


class ApplicationEventPublisher(metaclass=ABCMeta):
    def publish_event(self, event: ApplicationEvent) -> None:
        self.publish_event_object(event)

    @abstractmethod
    def publish_event_object(self, event: Any) -> None:
        ...

from typing import Set, Any, Type
from unittest import TestCase

from common.application_event_publisher import ApplicationEventPublisher
from contracts.model.state.dynamic.config.events.document_event import DocumentEvent


class FakeDocumentPublisher(ApplicationEventPublisher, TestCase):
    events: Set[Any]

    def __init__(self):
        super().__init__()
        self.events = set()

    def publish_event_object(self, event: Any):
        self.events.add(event)

    def contains(self, event: Type[DocumentEvent]):
        found: bool = any(map(lambda e: isinstance(e, event), self.events))
        self.assertTrue(found)

    def no_events(self):
        self.assertEqual(0, len(self.events))

    def reset(self):
        self.events = set()

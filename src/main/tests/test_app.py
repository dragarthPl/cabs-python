from unittest import TestCase

from starlette.testclient import TestClient

from cabs_application import CabsApplication


class TestApp(TestCase):
    def setUp(self) -> None:
        self.client = TestClient(CabsApplication().create_app())

    def test_read_main(self):
        response = self.client.get("/transits/0")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"msg": "Hello World"})

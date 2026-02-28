import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from importlib import import_module
from utils import find_package_name

class TestCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pkg_name = find_package_name()
        cls.core = import_module(f"{cls.pkg_name}")
        cls.router = cls.core.router
        cls.prefix = cls.core.prefix

        cls.app = FastAPI()
        cls.app.include_router(
            cls.router,
            prefix=f"/api/{cls.prefix}"
        )
        cls.client = TestClient(cls.app)

    def test_read_main(self):
        response = self.client.get(f"/api/{self.prefix}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["detail"], "OK")

    def test_read_example(self): # placeholder for real test cases
        response = self.client.get(f"/api/{self.prefix}/user")
        self.assertEqual(response.status_code, 200)
        json_dict = response.json()
        self.assertEqual(json_dict["message"], "User information")
        self.assertEqual(json_dict["detail"], {
            "id": 0,
            "email": "user@example.com",
            "role": "user"
        })
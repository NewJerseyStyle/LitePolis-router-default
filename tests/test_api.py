import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from importlib import import_module
from utils import find_package_name

class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pkg_name = find_package_name()
        cls.core = import_module(f"{cls.pkg_name}")
        cls.router = cls.core.router
        # The original Node.js tests use /api/v3/testConnection and /api/v3/testDatabase.
        # The Python tests in test_core.py use /api/{self.prefix}.
        # Assuming the /api/v3 part is fixed and not dynamic based on prefix for these specific tests.
        # If the prefix is 'v3', then it matches. If not, we need to adjust.
        # For now, I'll hardcode 'v3' as per the Node.js tests.
        # If the router itself has a prefix, it will be included.
        # Let's assume the router itself is mounted at /api/v3.
        # Based on test_core.py, the prefix is used in the include_router.
        # So, the full path would be /api/{cls.prefix}/testConnection.
        # The Node.js tests use /api/v3/testConnection. This implies that the router's prefix is 'v3'.
        # Let's use the cls.prefix from the imported module.
        cls.prefix = cls.core.prefix

        cls.app = FastAPI()
        cls.app.include_router(
            cls.router,
            prefix=f"/api/{cls.prefix}"
        )
        cls.client = TestClient(cls.app)

    def test_testConnection(self):
        response = self.client.get(f"/api/{self.prefix}/testConnection")
        self.assertEqual(response.status_code, 200)

    def test_testDatabase(self):
        response = self.client.get(f"/api/{self.prefix}/testDatabase")
        self.assertEqual(response.status_code, 200)
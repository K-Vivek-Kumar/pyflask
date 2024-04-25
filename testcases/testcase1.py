import unittest
from flask import jsonify
from flask_jwt_extended import create_access_token, JWTManager
from flask_testing import TestCase

from server import app


class TestAdminHomeRoute(TestCase):
    def create_app(self):
        app.config["TESTING"] = True
        app.config["JWT_SECRET_KEY"] = "test_secret_key"
        JWTManager(app)
        return app

    def test_admin_home_route_with_valid_token(self):
        admin_token = create_access_token(
            identity={"type": "admin", "key": "admin_key"}
        )
        response = self.client.get(
            "/admin-home", headers={"Authorization": f"Bearer {admin_token}"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json, {"admin": "admin_key"})

    def test_admin_home_route_with_invalid_token(self):
        invalid_token = create_access_token(
            identity={"type": "user", "key": "user_key"}
        )
        response = self.client.get(
            "/admin-home", headers={"Authorization": f"Bearer {invalid_token}"}
        )
        self.assertEqual(response.status_code, 403)
        self.assertDictEqual(response.json, {"error": "Protected Route"})


if __name__ == "__main__":
    unittest.main()

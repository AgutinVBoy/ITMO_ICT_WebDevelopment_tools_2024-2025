import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus


class TestAuthIntegration:
    def test_register_new_user_success(self, client: TestClient):
        """Полный цикл регистрации пользователя."""
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "PassW0rd"
        }

        response = client.post("/auth/register", json=user_data)

        assert response.status_code == HTTPStatus.CREATED
        json_data = response.json()
        assert "user" in json_data
        assert "access_token" in json_data
        assert json_data["user"]["username"] == "newuser"

    def test_register_duplicate_username_fails(self, client: TestClient):
        """Проверяет что дубликат username возвращает ошибку."""
        user1_data = {
            "username": "foobar",
            "email": "user1@example.com",
            "password": "PassW0rd"
        }
        user2_data = {
            "username": "foobar",
            "email": "user2@example.com",
            "password": "PassW0rd"
        }

        client.post("/auth/register", json=user1_data)
        response = client.post("/auth/register", json=user2_data)

        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        json_data = response.json()
        assert "errors" in json_data
        assert "username" in json_data["errors"]

    def test_register_invalid_password_fails(self, client: TestClient):
        """Проверяет валидацию пароля."""
        # В одном регистре
        response = client.post("/auth/register", json={
            "username": "foobar",
            "email": "user1@example.com",
            "password": "passw0rd"
        })
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "password" in response.json()["errors"]

        response = client.post("/auth/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "PASSW0RD"
        })
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "password" in response.json()["errors"]

        # Без цифр
        response = client.post("/auth/register", json={
            "username": "testuser2",
            "email": "test2@example.com",
            "password": "NoDigits?"
        })
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
        assert "password" in response.json()["errors"]



    def test_login_with_username_success(self, client: TestClient):
        """Проверяет авторизацию после регистрации."""
        client.post("/auth/register", json={
            "username": "johndoe",
            "email": "login@example.com",
            "password": "PassW0rd"
        })

        response = client.post("/auth/login", json={
            "login": "johndoe",
            "password": "PassW0rd"
        })

        assert response.status_code == HTTPStatus.OK
        json_data = response.json()
        assert "access_token" in json_data
        assert json_data["user"]["username"] == "johndoe"

    def test_login_wrong_password_fails(self, client: TestClient):
        """Проверяет что неправильный пароль возвращает 401."""
        client.post("/auth/register", json={
            "username": "wrongpass",
            "email": "wrong@example.com",
            "password": "PassW0rd"
        })

        response = client.post("/auth/login", json={
            "login": "wrongpass",
            "password": "foobar"
        })

        assert response.status_code == HTTPStatus.UNAUTHORIZED

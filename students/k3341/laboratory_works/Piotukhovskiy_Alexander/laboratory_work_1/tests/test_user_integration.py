import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus


class TestUserIntegration:
    def test_get_current_user_authenticated(self, client: TestClient):
        """Проверяет получение данных пользователя с токеном."""
        # Arrange
        reg_response = client.post("/auth/register", json={
            "username": "authuser",
            "email": "auth@example.com",
            "first_name": "Auth",
            "last_name": "User",
            "password": "PassW0rd"
        })
        token = reg_response.json()["access_token"]

        # Act
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == HTTPStatus.OK
        json_data = response.json()
        assert json_data["username"] == "authuser"
        assert json_data["email"] == "auth@example.com"
        assert json_data["first_name"] == "Auth"

    def test_get_current_user_without_token_fails(self, client: TestClient):
        """Проверяет, что запрос без токена возвращает 403."""
        response = client.get("/users/me")
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_update_current_user_info_success(self, client: TestClient):
        """Проверяет обновление информации о пользователе."""
        # Arrange
        reg_response = client.post("/auth/register", json={
            "username": "updateuser",
            "email": "update@example.com",
            "password": "PassW0rd"
        })
        token = reg_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = client.patch("/users/me", json={
            "first_name": "Updated",
            "last_name": "Name",
            "age": 30
        }, headers=headers)

        assert response.status_code == HTTPStatus.OK
        assert response.json()["first_name"] == "Updated"
        assert response.json()["last_name"] == "Name"

    def test_update_user_to_existing_username_fails(self, client: TestClient):
        """Проверяет что нельзя изменить username на существующий."""
        # Arrange
        client.post("/auth/register", json={
            "username": "existing",
            "email": "existing@example.com",
            "password": "PassW0rd"
        })

        reg2 = client.post("/auth/register", json={
            "username": "another",
            "email": "another@example.com",
            "password": "PassW0rd"
        })
        token2 = reg2.json()["access_token"]

        # Act
        response = client.patch("/users/me", json={
            "username": "existing"
        }, headers={"Authorization": f"Bearer {token2}"})

        # Assert
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

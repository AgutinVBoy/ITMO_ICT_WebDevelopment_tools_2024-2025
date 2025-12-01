import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus
from datetime import datetime, timedelta


class TestTripIntegration:
    def test_create_trip_authenticated_user(self, client: TestClient):
        """Проверяет создание поездки."""
        reg_response = client.post("/auth/register", json={
            "username": "tripcreator",
            "email": "creator@example.com",
            "password": "PassW0rd"
        })
        token = reg_response.json()["access_token"]

        # Create trip
        trip_data = {
            "title": "Тестовая поездка",
            "description": "Ибо в настоящую не поехать",
            "departure": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "arrival": (datetime.utcnow() + timedelta(days=10)).isoformat(),
            "departure_location": "Saint-Petersburg",
            "arrival_location": "Moscow"
        }

        response = client.post(
            "/trip",
            json=trip_data,
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == HTTPStatus.CREATED
        assert response.json()["title"] == "Тестовая поездка"

    def test_get_trip_details_with_participants(self, client: TestClient):
        """Проверяет получение деталей поездки."""
        reg_response = client.post("/auth/register", json={
            "username": "tripowner",
            "email": "owner@example.com",
            "password": "PassW0rd"
        })
        token = reg_response.json()["access_token"]

        trip_response = client.post("/trip", json={
            "title": "Ещё одна поездка",
            "description": "Тест",
            "departure": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "departure_location": "X",
            "arrival_location": "Y"
        }, headers={"Authorization": f"Bearer {token}"})

        trip_id = trip_response.json()["id"]

        # Act
        response = client.get(f"/trip/{trip_id}")

        assert response.status_code == HTTPStatus.OK
        json_data = response.json()
        assert "creator" in json_data
        assert "participants" in json_data
        assert json_data["creator"]["username"] == "tripowner"

    def test_update_trip_by_creator_success(self, client: TestClient):
        """Проверяет обновление поездки."""
        reg_response = client.post("/auth/register", json={
            "username": "updater",
            "email": "updater@example.com",
            "password": "PassW0rd"
        })
        token = reg_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        trip_response = client.post("/trip", json={
            "title": "Оригинал",
            "description": "Тест",
            "departure": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "departure_location": "X",
            "arrival_location": "Y"
        }, headers=headers)

        trip_id = trip_response.json()["id"]
        trip_departure = trip_response.json()["departure"]

        # Act
        response = client.put(f"/trip/{trip_id}", json={
            "title": "Обновили заголовок",
            "description": "Обновили и описание",
            "departure": trip_departure,
            "departure_location": "X",
            "arrival_location": "Z"
        }, headers=headers)

        assert response.status_code == HTTPStatus.OK
        assert response.json()["title"] == "Обновили заголовок"

    def test_update_trip_by_non_creator_fails(self, client: TestClient):
        """Проверяет что НЕ создатель не может обновить поездку."""
        # Пользователь 1, автор поездки
        reg1 = client.post("/auth/register", json={
            "username": "creator1",
            "email": "creator1@example.com",
            "password": "PassW0rd"
        })
        token1 = reg1.json()["access_token"]

        trip_response = client.post("/trip", json={
            "title": "Поездка креатора",
            "description": "Тест",
            "departure": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "departure_location": "A",
            "arrival_location": "B"
        }, headers={"Authorization": f"Bearer {token1}"})

        trip_id = trip_response.json()["id"]
        trip_departure = trip_response.json()["departure"]

        # Пользователь 2, случайный
        reg2 = client.post("/auth/register", json={
            "username": "fake_creator",
            "email": "fake_creator@example.com",
            "password": "PassW0rd"
        })
        token2 = reg2.json()["access_token"]

        response = client.put(f"/trip/{trip_id}", json={
            "title": "Дешевые авиабилеты?",
            "description": "Отель?",
            "departure": trip_departure,
            "departure_location": "А",
            "arrival_location": "Я"
        }, headers={"Authorization": f"Bearer {token2}"})

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_subscribe_twice_fails(self, client: TestClient):
        """Проверяет что нельзя подписаться дважды."""
        # Автор
        reg1 = client.post("/auth/register", json={
            "username": "another_creator",
            "email": "another_creator@example.com",
            "password": "PassW0rd"
        })
        token1 = reg1.json()["access_token"]

        trip_response = client.post("/trip", json={
            "title": "Поездка креатора",
            "description": "Тест",
            "departure": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "departure_location": "A",
            "arrival_location": "B"
        }, headers={"Authorization": f"Bearer {token1}"})

        trip_id = trip_response.json()["id"]

        # Обычный участник
        reg2 = client.post("/auth/register", json={
            "username": "passenger",
            "email": "passenger@example.com",
            "password": "PassW0rd"
        })
        token2 = reg2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Первая подписка
        response1 = client.post(f"/trip/{trip_id}/subscribe", headers=headers2)
        assert response1.status_code == HTTPStatus.CREATED

        # Вторая подписка
        response2 = client.post(f"/trip/{trip_id}/subscribe", headers=headers2)
        assert response2.status_code == HTTPStatus.CONFLICT

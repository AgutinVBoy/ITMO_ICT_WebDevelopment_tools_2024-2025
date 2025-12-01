import pytest
from fastapi.testclient import TestClient
from http import HTTPStatus
from datetime import datetime, timedelta


class TestComplexScenarios:
    def test_sql_injection_prevention(self, client: TestClient):
        """Проверяет защиту от SQL инъекции."""
        response = client.get("/trip/search", params={
            "title": "'; DROP TABLE user; --"
        })

        # Система ответила что-то корректное
        assert response.status_code in [HTTPStatus.OK, HTTPStatus.UNPROCESSABLE_ENTITY]

        # Система должна нормально функционировать
        reg = client.post("/auth/register", json={
            "username": "afterinjection",
            "email": "after@test.com",
            "password": "AfterPass123"
        })
        assert reg.status_code == HTTPStatus.CREATED

    def test_full_trip_lifecycle(self, client: TestClient):
        """
        Полный жизненный цикл поездки:
        Регистрация, Создание, Подписка, Обновление, Отписка
        """
        # User A (автор)
        reg_a = client.post("/auth/register", json={
            "username": "userA",
            "email": "a@example.com",
            "password": "PassW0rd"
        })
        token_a = reg_a.json()["access_token"]

        # User B (участник)
        reg_b = client.post("/auth/register", json={
            "username": "userB",
            "email": "b@example.com",
            "password": "PassW0rd"
        })
        token_b = reg_b.json()["access_token"]

        # Создание поездки
        trip_resp = client.post("/trip", json={
            "title": "Жизненный цикл поездки",
            "description": "Полный тест сервиса",
            "departure": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "departure_location": "A",
            "arrival_location": "B"
        }, headers={"Authorization": f"Bearer {token_a}"})

        assert trip_resp.status_code == HTTPStatus.CREATED
        trip_id = trip_resp.json()["id"]

        # User B подписывается
        sub_resp = client.post(
            f"/trip/{trip_id}/subscribe",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert sub_resp.status_code == HTTPStatus.CREATED

        # Проверка участников
        details = client.get(f"/trip/{trip_id}")
        assert len(details.json()["participants"]) == 1

        # User A меняет информацию о поездке
        update_resp = client.put(f"/trip/{trip_id}", json={
            "title": "Обновили название",
            "description": "И описание",
            "departure": trip_resp.json()["departure"],
            "departure_location": "X",
            "arrival_location": "Y"
        }, headers={"Authorization": f"Bearer {token_a}"})
        assert update_resp.status_code == HTTPStatus.OK

        # User B отписывается
        unsub_resp = client.delete(
            f"/trip/{trip_id}/subscribe",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert unsub_resp.status_code == HTTPStatus.NO_CONTENT

        # Проверка участников
        details2 = client.get(f"/trip/{trip_id}")
        assert len(details2.json()["participants"]) == 0

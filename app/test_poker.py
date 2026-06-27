"""Integration tests for the Poker Tournament Manager API.

Tests verify:
- database-backed persistence
- route docstrings
- user creation and validation
- duplicate username/email/card checks
- balance deposit flow
- poker tournament creation and update
- tournament registration
- insufficient balance handling
- late registration closing
- registration listing and deletion
"""

import importlib
import inspect

import requests


BASE_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

USER = {
    "username": "player1",
    "name": "Mario Rossi",
    "email": "mario@example.com",
    "numero_carta": "1234567890123456",
    "cvv_carta": "123",
}

USER2 = {
    "username": "player2",
    "name": "Luigi Verdi",
    "email": "luigi@example.com",
    "numero_carta": "6543210987654321",
    "cvv_carta": "321",
}

DEPOSIT = {
    "card_holder": "Mario Rossi",
    "card_number": "1234567890123456",
    "card_cvv": "123",
    "amount": 50,
}

EVENT = {
    "title": "Sunday Poker MTT",
    "description": "Torneo Texas Hold'em",
    "date": "2026-06-01T20:00:00",
    "location": "Online",
    "chips": 10000,
    "buy_in": 5,
    "montepremi": 500,
    "end_late_reg": "2026-06-01T21:00:00",
}

EVENT_UPDATED = {
    "title": "Updated Poker MTT",
    "description": "Torneo aggiornato",
    "date": "2026-07-01T21:00:00",
    "location": "Poker Room",
    "chips": 15000,
    "buy_in": 10,
    "montepremi": 1000,
    "end_late_reg": "2026-07-01T22:00:00",
}

EVENT_LATE_CLOSED = {
    "title": "Closed Late Reg",
    "description": "Torneo con registrazione chiusa",
    "date": "2025-06-01T20:00:00",
    "location": "Online",
    "chips": 10000,
    "buy_in": 5,
    "montepremi": 500,
    "end_late_reg": "2025-06-01T21:00:00",
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def GET(path):
    """Execute a GET request."""
    return requests.get(BASE_URL + path)


def POST(path, data):
    """Execute a POST request with JSON data."""
    return requests.post(BASE_URL + path, json=data)


def PUT(path, data):
    """Execute a PUT request with JSON data."""
    return requests.put(BASE_URL + path, json=data)


def DELETE(path):
    """Execute a DELETE request."""
    return requests.delete(BASE_URL + path)


def clean_db():
    """Remove all test data before each test."""
    for registration in GET("/registrations").json():
        DELETE(
            f"/registrations?"
            f"username={registration['username']}"
            f"&event_id={registration['event_id']}"
        )

    for user in GET("/users").json():
        DELETE(f"/users/{user['username']}")

    for event in GET("/events").json():
        DELETE(f"/events/{event['id']}")


# ===========================================================================
# 0. STRUCTURAL CHECKS
# ===========================================================================

def test_database_is_used():
    """Verify that the application uses a file-based SQLite database."""
    from app.data import db as db_module

    url = str(db_module.engine.url)
    assert ":memory:" not in url


def test_all_routes_have_docstrings():
    """Verify that every router endpoint has a docstring."""
    router_modules = [
        "app.routers.events",
        "app.routers.users",
        "app.routers.registrations",
    ]

    missing = []

    for mod_name in router_modules:
        mod = importlib.import_module(mod_name)

        for route in mod.router.routes:
            fn = route.endpoint
            if not inspect.getdoc(fn):
                missing.append(f"{mod_name}: {fn.__name__}")

    assert not missing


# ===========================================================================
# 1. USERS
# ===========================================================================

def test_users_list_returns_list():
    """GET /users must return a JSON list."""
    clean_db()

    response = GET("/users")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user_valid():
    """POST /users with valid data must create a new user."""
    clean_db()

    response = POST("/users", USER)

    assert response.status_code in (200, 201)

    users = GET("/users").json()
    assert any(user["username"] == USER["username"] for user in users)


def test_create_user_missing_name():
    """POST /users without name must return 422."""
    clean_db()

    bad = dict(USER)
    del bad["name"]

    response = POST("/users", bad)

    assert response.status_code == 422


def test_create_user_missing_card():
    """POST /users without card number must return 422."""
    clean_db()

    bad = dict(USER)
    del bad["numero_carta"]

    response = POST("/users", bad)

    assert response.status_code == 422


def test_create_user_invalid_card_length():
    """POST /users with an invalid card number length must fail."""
    clean_db()

    bad = dict(USER)
    bad["numero_carta"] = "123"

    response = POST("/users", bad)

    assert response.status_code in (400, 422)


def test_create_user_invalid_card_letters():
    """POST /users with letters in the card number must fail."""
    clean_db()

    bad = dict(USER)
    bad["numero_carta"] = "12345678901234AB"

    response = POST("/users", bad)

    assert response.status_code in (400, 422)


def test_create_user_invalid_cvv_length():
    """POST /users with an invalid CVV length must fail."""
    clean_db()

    bad = dict(USER)
    bad["cvv_carta"] = "12"

    response = POST("/users", bad)

    assert response.status_code in (400, 422)


def test_create_user_invalid_cvv_letters():
    """POST /users with letters in the CVV must fail."""
    clean_db()

    bad = dict(USER)
    bad["cvv_carta"] = "1A3"

    response = POST("/users", bad)

    assert response.status_code in (400, 422)


def test_create_user_duplicate_username():
    """POST /users with an existing username must fail."""
    clean_db()

    POST("/users", USER)
    response = POST("/users", USER)

    assert 400 <= response.status_code < 500


def test_create_user_duplicate_email():
    """POST /users with an existing email must fail."""
    clean_db()

    POST("/users", USER)

    bad = dict(USER2)
    bad["email"] = USER["email"]

    response = POST("/users", bad)

    assert 400 <= response.status_code < 500


def test_create_user_duplicate_card():
    """POST /users with an existing card number must fail."""
    clean_db()

    POST("/users", USER)

    bad = dict(USER2)
    bad["numero_carta"] = USER["numero_carta"]

    response = POST("/users", bad)

    assert 400 <= response.status_code < 500


def test_get_user_by_username():
    """GET /users/{username} must return the correct user."""
    clean_db()

    POST("/users", USER)

    response = GET(f"/users/{USER['username']}")

    assert response.status_code == 200
    assert response.json()["username"] == USER["username"]


def test_get_user_not_found():
    """GET /users/{username} with a missing user must return 404."""
    clean_db()

    response = GET("/users/not_existing_user")

    assert response.status_code == 404


def test_delete_user():
    """DELETE /users/{username} must remove the user."""
    clean_db()

    POST("/users", USER)

    response = DELETE(f"/users/{USER['username']}")

    assert response.status_code == 200
    assert GET(f"/users/{USER['username']}").status_code == 404


def test_delete_user_not_found():
    """DELETE /users/{username} with a missing user must return 404."""
    clean_db()

    response = DELETE("/users/not_existing_user")

    assert response.status_code == 404


# ===========================================================================
# 2. DEPOSITS
# ===========================================================================

def test_deposit_valid():
    """POST /users/{username}/deposit must increase the user balance."""
    clean_db()

    POST("/users", USER)

    response = POST(f"/users/{USER['username']}/deposit", DEPOSIT)

    assert response.status_code == 200
    assert response.json()["saldo"] >= DEPOSIT["amount"]


def test_deposit_invalid_card_holder():
    """POST /users/{username}/deposit with a wrong holder must fail."""
    clean_db()

    POST("/users", USER)

    bad = dict(DEPOSIT)
    bad["card_holder"] = "Nome Sbagliato"

    response = POST(f"/users/{USER['username']}/deposit", bad)

    assert 400 <= response.status_code < 500


def test_deposit_invalid_card_number():
    """POST /users/{username}/deposit with a wrong card number must fail."""
    clean_db()

    POST("/users", USER)

    bad = dict(DEPOSIT)
    bad["card_number"] = "1111222233334444"

    response = POST(f"/users/{USER['username']}/deposit", bad)

    assert 400 <= response.status_code < 500


def test_deposit_invalid_cvv():
    """POST /users/{username}/deposit with a wrong CVV must fail."""
    clean_db()

    POST("/users", USER)

    bad = dict(DEPOSIT)
    bad["card_cvv"] = "999"

    response = POST(f"/users/{USER['username']}/deposit", bad)

    assert 400 <= response.status_code < 500


def test_deposit_negative_amount():
    """POST /users/{username}/deposit with a negative amount must fail."""
    clean_db()

    POST("/users", USER)

    bad = dict(DEPOSIT)
    bad["amount"] = -10

    response = POST(f"/users/{USER['username']}/deposit", bad)

    assert 400 <= response.status_code < 500


# ===========================================================================
# 3. EVENTS / TOURNAMENTS
# ===========================================================================

def test_events_list_returns_list():
    """GET /events must return a JSON list."""
    clean_db()

    response = GET("/events")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_event_valid():
    """POST /events with valid data must create a poker tournament."""
    clean_db()

    response = POST("/events", EVENT)

    assert response.status_code in (200, 201)

    events = GET("/events").json()
    assert any(event["title"] == EVENT["title"] for event in events)


def test_create_event_missing_buy_in():
    """POST /events without buy_in must return 422."""
    clean_db()

    bad = dict(EVENT)
    del bad["buy_in"]

    response = POST("/events", bad)

    assert response.status_code == 422


def test_create_event_missing_chips():
    """POST /events without chips must return 422."""
    clean_db()

    bad = dict(EVENT)
    del bad["chips"]

    response = POST("/events", bad)

    assert response.status_code == 422


def test_get_event_by_id():
    """GET /events/{id} must return the correct tournament."""
    clean_db()

    POST("/events", EVENT)
    event_id = GET("/events").json()[0]["id"]

    response = GET(f"/events/{event_id}")

    assert response.status_code == 200
    assert response.json()["title"] == EVENT["title"]


def test_get_event_not_found():
    """GET /events/{id} with a missing tournament must return 404."""
    clean_db()

    response = GET("/events/999999")

    assert response.status_code == 404


def test_update_event_valid():
    """PUT /events/{id} must update a tournament."""
    clean_db()

    POST("/events", EVENT)
    event_id = GET("/events").json()[0]["id"]

    response = PUT(f"/events/{event_id}", EVENT_UPDATED)

    assert response.status_code == 200

    updated = GET(f"/events/{event_id}").json()
    assert updated["title"] == EVENT_UPDATED["title"]
    assert updated["buy_in"] == EVENT_UPDATED["buy_in"]


def test_update_event_not_found():
    """PUT /events/{id} with a missing tournament must return 404."""
    clean_db()

    response = PUT("/events/999999", EVENT_UPDATED)

    assert response.status_code == 404


def test_delete_event():
    """DELETE /events/{id} must remove the tournament."""
    clean_db()

    POST("/events", EVENT)
    event_id = GET("/events").json()[0]["id"]

    response = DELETE(f"/events/{event_id}")

    assert response.status_code == 200
    assert GET(f"/events/{event_id}").status_code == 404


def test_delete_event_not_found():
    """DELETE /events/{id} with a missing tournament must return 404."""
    clean_db()

    response = DELETE("/events/999999")

    assert response.status_code == 404


# ===========================================================================
# 4. REGISTRATIONS
# ===========================================================================

def test_registrations_list_returns_list():
    """GET /registrations must return a JSON list."""
    clean_db()

    response = GET("/registrations")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_register_to_event_valid():
    """POST /events/{id}/register must register the user to the tournament."""
    clean_db()

    POST("/users", USER)
    POST(f"/users/{USER['username']}/deposit", DEPOSIT)

    POST("/events", EVENT)
    event_id = GET("/events").json()[0]["id"]

    response = POST(f"/events/{event_id}/register", USER)

    assert response.status_code in (200, 201)

    registrations = GET("/registrations").json()

    assert any(
        registration["username"] == USER["username"]
        and registration["event_id"] == event_id
        for registration in registrations
    )


def test_register_duplicate():
    """POST /events/{id}/register twice must not create a server error."""
    clean_db()

    POST("/users", USER)
    POST(f"/users/{USER['username']}/deposit", DEPOSIT)

    POST("/events", EVENT)
    event_id = GET("/events").json()[0]["id"]

    POST(f"/events/{event_id}/register", USER)
    response = POST(f"/events/{event_id}/register", USER)

    assert response.status_code < 500


def test_register_insufficient_balance():
    """POST /events/{id}/register with insufficient balance must fail."""
    clean_db()

    POST("/users", USER)
    POST("/events", EVENT)

    event_id = GET("/events").json()[0]["id"]

    response = POST(f"/events/{event_id}/register", USER)

    assert 400 <= response.status_code < 500


def test_register_late_registration_closed():
    """POST /events/{id}/register after late registration ends must fail."""
    clean_db()

    POST("/users", USER)
    POST(f"/users/{USER['username']}/deposit", DEPOSIT)

    POST("/events", EVENT_LATE_CLOSED)
    event_id = GET("/events").json()[0]["id"]

    response = POST(f"/events/{event_id}/register", USER)

    assert 400 <= response.status_code < 500


def test_delete_registration():
    """DELETE /registrations must remove the specified registration."""
    clean_db()

    POST("/users", USER)
    POST(f"/users/{USER['username']}/deposit", DEPOSIT)

    POST("/events", EVENT)
    event_id = GET("/events").json()[0]["id"]

    POST(f"/events/{event_id}/register", USER)

    response = DELETE(
        f"/registrations?username={USER['username']}&event_id={event_id}"
    )

    assert response.status_code == 200

    registrations = GET("/registrations").json()

    assert not any(
        registration["username"] == USER["username"]
        and registration["event_id"] == event_id
        for registration in registrations
    )


def test_delete_registration_user_not_found():
    """DELETE /registrations with a missing user must return 404."""
    clean_db()

    POST("/events", EVENT)
    event_id = GET("/events").json()[0]["id"]

    response = DELETE(
        f"/registrations?username=missing_user&event_id={event_id}"
    )

    assert response.status_code == 404


def test_delete_registration_event_not_found():
    """DELETE /registrations with a missing event must return 404."""
    clean_db()

    POST("/users", USER)

    response = DELETE(
        f"/registrations?username={USER['username']}&event_id=999999"
    )

    assert response.status_code == 404
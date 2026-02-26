def test_login_success_sets_session_and_redirects(client, fake_db):
    fake_db.set_one({"first_name": "Elli", "email": "a@b.com"})

    resp = client.post(
        "/login",
        data={"email": "A@B.COM", "password": "123"},
        follow_redirects=False
    )

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")

    with client.session_transaction() as sess:
        assert sess["user_email"] == "a@b.com"
        assert sess["user_name"] == "Elli"


def test_login_failure_shows_error(client, fake_db):
    fake_db.set_one(None)

    resp = client.post(
        "/login",
        data={"email": "x@y.com", "password": "bad"},
        follow_redirects=True
    )

    assert resp.status_code == 200
    assert b"Invalid email or password" in resp.data
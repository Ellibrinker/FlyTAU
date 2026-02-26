def test_homepage_ok_for_regular_user(client):
    resp = client.get("/")
    assert resp.status_code == 200

def test_homepage_redirects_for_manager(client):
    with client.session_transaction() as sess:
        sess["is_manager"] = True
    resp = client.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/admin/")
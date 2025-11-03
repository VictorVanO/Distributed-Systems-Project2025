# test_app.py
import unittest
from unittest.mock import patch
from app import app

class FakeCursor:
    def __init__(self, storage, mode='select'):
        self.storage = storage      # liste de dicts {'name','email','phone'}
        self.mode = mode            # 'select' ou 'insert'
        self.last_query = None
        self.last_params = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    # Emule cur.execute(...) minimal pour nos tests
    def execute(self, query, params=None):
        self.last_query = query
        self.last_params = params
        q = query.strip().lower()

        # DDL (CREATE TABLE IF NOT EXISTS ...) : no-op
        if q.startswith("create table"):
            return

        # INSERT INTO contacts (...)
        if q.startswith("insert into contacts"):
            # params = (name, email, phone)
            name, email, phone = params
            # on ajoute en fin ; id auto simulé = len+1
            self.storage.append({"name": name, "email": email, "phone": phone})
            return

        # SELECT ... FROM contacts ...
        if q.startswith("select"):
            # rien à faire ici, fetchall() renverra depuis storage
            return

    def fetchall(self):
        # retourne les lignes comme tuples (name, email, phone)
        # tri "ORDER BY id DESC" -> on simule par l'ordre d'insertion inverse
        rows = list(reversed(self.storage))
        return [(r["name"], r["email"], r["phone"]) for r in rows]


class FakeConn:
    def __init__(self, shared_storage):
        # shared_storage est une liste partagée entre connexions
        self._storage = shared_storage

    def cursor(self):
        # un cursor qui connaît le storage partagé
        return FakeCursor(self._storage)

    def close(self):
        pass


class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True

        # Un "storage" partagé pour simuler la table contacts
        # On pré-remplit côté "shard 0" et "shard 1" pour GET /
        # NB : on simulera deux connexions (s0 et s1) pointant sur le même storage
        # pour simplifier, mais on ajoute des entrées distinctes pour mimer 2 shards.
        self.shared_storage_s0 = [
            {"name": "Alice Dupont", "email": "alice@mail.com", "phone": "+32 475 11 22 33"},
        ]
        self.shared_storage_s1 = [
            {"name": "Karim Amrani", "email": "karim@example.org", "phone": "+32 484 44 55 66"},
        ]

        # Fabrique qui renvoie alternativement une connexion s0 puis s1,
        # car app.py appelle connect() deux fois (s0 puis s1) pour le GET /
        self._connect_call_index = 0

        def fake_connect_factory(uri: str):
            # On décide s0/s1 selon l'URI (comme dans app.py)
            if "mysql_s0_primary" in uri:
                return FakeConn(self.shared_storage_s0)
            if "mysql_s1_primary" in uri:
                return FakeConn(self.shared_storage_s1)
            # fallback (ne devrait pas arriver)
            return FakeConn(self.shared_storage_s0)

        self.fake_connect_factory = fake_connect_factory

    @patch("app.connect")
    def test_health_route(self, mock_connect):
        # /health ne touche pas la DB, mais on patch quand même par cohérence
        mock_connect.side_effect = self.fake_connect_factory
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"ok", res.data)

    @patch("app.connect")
    def test_home_route_get_lists_contacts_from_both_shards(self, mock_connect):
        mock_connect.side_effect = self.fake_connect_factory
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        # On doit voir des noms provenant des deux "shards"
        self.assertIn(b"Alice Dupont", res.data)   # s0
        self.assertIn(b"Karim Amrani", res.data)   # s1
        self.assertIn(b"Carnet de contacts", res.data)

    @patch("app.shard_from_email", return_value=0)  # force shard 0
    @patch("app.connect")
    def test_add_contact_inserts_and_is_visible(self, mock_connect, mock_shard):
        mock_connect.side_effect = self.fake_connect_factory

        payload = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+32 400 00 00 00",
        }
        res = self.client.post("/", data=payload, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        # l'utilisateur doit apparaître dans le HTML après redirection
        self.assertIn(b"Test User", res.data)
        self.assertIn(b"test@example.com", res.data)

        # la ligne a bien été insérée dans le storage shard 0
        self.assertTrue(any(r["email"] == "test@example.com" for r in self.shared_storage_s0))

    @patch("app.connect")
    def test_post_missing_fields_returns_400(self, mock_connect):
        mock_connect.side_effect = self.fake_connect_factory

        # manque email
        res = self.client.post("/", data={"name": "No Email", "phone": "000"}, follow_redirects=False)
        self.assertEqual(res.status_code, 400)

        # manque name
        res2 = self.client.post("/", data={"email": "no@name", "phone": "000"}, follow_redirects=False)
        self.assertEqual(res2.status_code, 400)


if __name__ == "__main__":
    unittest.main()

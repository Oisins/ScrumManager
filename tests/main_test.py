import unittest
from app import create_app
from app.models import db, User


class TestScrumManager(unittest.TestCase):
    def login(self, user_id):
        return self.app.post('/login', data=dict(
            user_id=user_id
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def setUp(self):
        app = create_app("testing")
        app.testing = True
        self.app = app.test_client()

    def test_login(self):
        u = User()
        u.name = "Bob"
        db.session.add(u)
        db.session.commit()

        resp = self.login(0)
        assert True


if __name__ == '__main__':
    unittest.main()

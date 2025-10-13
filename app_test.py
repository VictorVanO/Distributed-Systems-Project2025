import unittest
from app import app, contacts

class TestFlaskApp(unittest.TestCase):
    
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Reset contact
        contacts.clear()
        contacts.extend([
            {"name": "Alice Dupont", "email": "alice@mail.com", "phone": "+32 475 11 22 33"},
            {"name": "Karim El Amrani", "email": "karim@example.org", "phone": "+32 484 44 55 66"},
        ])
    
    def test_home_route_get(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Carnet de contacts', response.data)
        self.assertIn(b'Alice Dupont', response.data)
    
    def test_add_contact(self):
        response = self.app.post('/', data={
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '+32 400 00 00 00'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test User', response.data)
    
    def test_404_route(self):
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
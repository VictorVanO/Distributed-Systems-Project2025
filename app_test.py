import unittest
from app import app

class TestFlaskApp(unittest.TestCase):
    
    def setUp(self):
        # Set up test client before each test
        self.app = app.test_client()
        self.app.testing = True
    
    def test_home_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'Distributed Systems Project 2025')
    
    def test_hello_route(self):
        response = self.app.get('/hello')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'Hello, World')
    
    def test_404_route(self):
        response = self.app.get('/nonexistent')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
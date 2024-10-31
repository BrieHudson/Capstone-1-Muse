import os
import unittest
from app import app, db, User, Post
from flask import session

class FlaskAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Setup a test client and database before any tests."""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///muse_test_db'  # Use a test database
        cls.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        cls.client = cls.app.test_client()
        with cls.app.app_context():
            db.create_all()  # Create the test database tables

    @classmethod
    def tearDownClass(cls):
        """Drop the test database after all tests."""
        with cls.app.app_context():
            db.session.remove()
            db.drop_all()  # Drop the test database tables

    def setUp(self):
        """Create a new user before each test."""
        with self.app.app_context():
            user = User.signup(
                username='testuser',
                email='test@example.com',
                password='testpassword'
            )
            db.session.commit()

    def tearDown(self):
        """Remove the user after each test."""
        with self.app.app_context():
            db.session.remove()

    def test_signup(self):
        """Test user signup."""
        response = self.client.post('/signup', data={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword'
        })
        self.assertEqual(response.status_code, 302)  # Check for redirect after signup
        self.assertIn(b'Account created successfully!', response.data)

    def test_login(self):
        """Test user login."""
        response = self.client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword'
        })
        self.assertEqual(response.status_code, 302)  # Check for redirect after login
        with self.client:
            self.client.get('/')  # Ensure user is logged in
            self.assertIn(session['curr_user'], [1])  # Replace with appropriate user ID

    def test_logout(self):
        """Test user logout."""
        with self.client:
            self.client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            response = self.client.get('/logout')
            self.assertEqual(response.status_code, 302)  # Check for redirect after logout
            with self.client:
                self.client.get('/')  # Ensure user is logged out
                self.assertNotIn(session, 'curr_user')

    def test_add_post(self):
        """Test adding a post."""
        with self.client:
            self.client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            response = self.client.post('/add_post', data={
                'selected_spotify_id': '12345',
                'spotify_name': 'Test Song',
                'artist_name': 'Test Artist',
                'caption': 'This is a test post.'
            })
            self.assertEqual(response.status_code, 302)  # Check for redirect after adding post
            post = Post.query.filter_by(spotify_name='Test Song').first()
            self.assertIsNotNone(post)  # Ensure the post is created

    def test_delete_post(self):
        """Test deleting a post."""
        with self.client:
            self.client.post('/login', data={
                'username': 'testuser',
                'password': 'testpassword'
            })
            post = Post(user_id=1, spotify_id='12345', spotify_name='Test Song', caption='This is a test post.')
            db.session.add(post)
            db.session.commit()
            response = self.client.post(f'/delete_post/{post.id}')
            self.assertEqual(response.status_code, 302)  # Check for redirect after deleting post
            deleted_post = Post.query.get(post.id)
            self.assertIsNone(deleted_post)  # Ensure the post is deleted

if __name__ == '__main__':
    unittest.main()

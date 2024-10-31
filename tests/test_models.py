import os
import unittest
from app import app
from models import db, User, Post, Follower, Like, Comment

class ModelsTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up a test client and database."""
        cls.app = create_app('testing')  
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Clean up the database."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def setUp(self):
        """Create a new user for testing."""
        self.user1 = User.signup(username="testuser1", email="test1@example.com", password="testpassword")
        self.user2 = User.signup(username="testuser2", email="test2@example.com", password="testpassword")
        db.session.commit()

    def tearDown(self):
        """Remove any data after each test."""
        db.session.remove()
        db.drop_all()
        db.create_all()

    def test_user_creation(self):
        """Test that a user can be created."""
        self.assertEqual(self.user1.username, "testuser1")
        self.assertEqual(self.user1.email, "test1@example.com")
        self.assertTrue(self.user1.password)

    def test_follow_user(self):
        """Test following a user."""
        self.user1.follow(self.user2)
        db.session.commit()
        self.assertTrue(self.user1.is_following(self.user2))

    def test_unfollow_user(self):
        """Test unfollowing a user."""
        self.user1.follow(self.user2)
        db.session.commit()
        self.user1.unfollow(self.user2)
        db.session.commit()
        self.assertFalse(self.user1.is_following(self.user2))

    def test_like_post(self):
        """Test liking a post."""
        post = Post(user_id=self.user1.id, spotify_id="12345", spotify_name="Test Song")
        db.session.add(post)
        db.session.commit()
        
        self.user1.like_post(post)
        db.session.commit()
        
        self.assertTrue(self.user1.has_liked_post(post))

    def test_unlike_post(self):
        """Test unliking a post."""
        post = Post(user_id=self.user1.id, spotify_id="12345", spotify_name="Test Song")
        db.session.add(post)
        db.session.commit()
        
        self.user1.like_post(post)
        db.session.commit()
        
        db.session.delete(Like.query.filter_by(user_id=self.user1.id, post_id=post.id).first())
        db.session.commit()

        self.assertFalse(self.user1.has_liked_post(post))

    def test_authentication(self):
        """Test user authentication."""
        authenticated_user = User.authenticate("testuser1", "testpassword")
        self.assertIsNotNone(authenticated_user)
        self.assertEqual(authenticated_user.username, "testuser1")

        # Test with wrong password
        wrong_auth_user = User.authenticate("testuser1", "wrongpassword")
        self.assertIsNone(wrong_auth_user)

    def test_post_creation(self):
        """Test creating a post."""
        post = Post(user_id=self.user1.id, spotify_id="12345", spotify_name="Test Song")
        db.session.add(post)
        db.session.commit()

        self.assertEqual(post.spotify_name, "Test Song")
        self.assertEqual(post.user_id, self.user1.id)

if __name__ == '__main__':
    unittest.main()

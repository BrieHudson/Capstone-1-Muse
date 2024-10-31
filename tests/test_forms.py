import unittest
from flask import Flask
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Email
from forms import PostForm, LoginForm, SignupForm, CommentForm, SearchForm  # Adjust the import as necessary

class FormTests(unittest.TestCase):

    def setUp(self):
        """Create a Flask application and test client."""
        self.app = Flask(__name__)
        self.app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """Cleanup after each test."""
        self.app_context.pop()

    def test_post_form_validation(self):
        """Test validation of the PostForm."""
        form = PostForm(data={})
        self.assertFalse(form.validate())  # Expect validation to fail without data
        self.assertIn("You must select a song or playlist.", form.spotify_name.errors)

        # Provide data to the form
        form = PostForm(data={
            'search_query': 'Test song',
            'selected_spotify_id': '12345',
            'spotify_name': 'Test song',
            'artist_name': 'Test artist',
            'caption': 'This is a test caption.',
        })
        self.assertTrue(form.validate())  # Expect validation to succeed

    def test_login_form_validation(self):
        """Test validation of the LoginForm."""
        form = LoginForm(data={})
        self.assertFalse(form.validate())  # Expect validation to fail without data
        self.assertIn("This field is required.", form.username.errors)
        self.assertIn("This field is required.", form.password.errors)

        # Provide valid data
        form = LoginForm(data={
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertTrue(form.validate())  # Expect validation to succeed

    def test_signup_form_validation(self):
        """Test validation of the SignupForm."""
        form = SignupForm(data={})
        self.assertFalse(form.validate())  # Expect validation to fail without data
        self.assertIn("This field is required.", form.username.errors)
        self.assertIn("This field is required.", form.email.errors)
        self.assertIn("This field is required.", form.password.errors)

        # Provide valid data
        form = SignupForm(data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        self.assertTrue(form.validate())  # Expect validation to succeed

    def test_comment_form_validation(self):
        """Test validation of the CommentForm."""
        form = CommentForm(data={})
        self.assertFalse(form.validate())  # Expect validation to fail without data
        self.assertIn("This field is required.", form.content.errors)

        # Provide valid data
        form = CommentForm(data={
            'content': 'This is a comment.'
        })
        self.assertTrue(form.validate())  # Expect validation to succeed

    def test_search_form_validation(self):
        """Test validation of the SearchForm."""
        form = SearchForm(data={})
        self.assertFalse(form.validate())  # Expect validation to fail without data
        self.assertIn("This field is required.", form.query.errors)

        # Provide valid data
        form = SearchForm(data={
            'query': 'search term'
        })
        self.assertTrue(form.validate())  # Expect validation to succeed

if __name__ == '__main__':
    unittest.main()

# post form
# comment form
# search form
# login / signup form
# connect to spotify form

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, Email, EqualTo


class PostForm(FlaskForm):
    search_query = StringField('Search for a song or playlist', render_kw={"placeholder": "Type to Search..."})
    
    #hidden field to store the selected spotify song/playlist ID
    selected_spotify_id = HiddenField('Selected Spotify ID', validators=[DataRequired()])
    spotify_name = HiddenField('Spotify Name')  # Stores song/playlist name
    artist_name = StringField('Artist Name')

    #common field for both types
    caption = TextAreaField('Caption', render_kw={"placeholder": "Type to search..."}, validators=[Length(max=280)])
    submit = SubmitField('Post')

    def validate(self, **kwargs):
        """Custom validation to ensure the correct fields are required based on the selected item"""
        rv = super().validate(**kwargs)
        if not rv:
            return False

         # Ensure that a Spotify item has been selected
        if not self.spotify_name.data:
            self.spotify_name.errors.append("You must select a song or playlist.")
            return False

        return True

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Sign Up')

class CommentForm(FlaskForm):
    content = StringField('Comment', validators=[DataRequired()])
    submit = SubmitField('Post')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')
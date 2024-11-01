from flask  import Flask
from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash

db = SQLAlchemy()
bcrypt = Bcrypt()

def connect_db(app):
    with app.app_context():
        db.app = app
        db.init_app(app)
        db.create_all()

"""def connect_db(app):
    db.app = app
    db.init_app(app)"""


class Follower(db.Model):
    __tablename__ = 'followers'

    id = db.Column(db.Integer, 
                    primary_key=True,
                    autoincrement=True)

    follower_id = db.Column(db.Integer,
                             db.ForeignKey('users.id'),
                             nullable=False)

    followed_id = db.Column(db.Integer,
                             db.ForeignKey('users.id'),
                             nullable=False)

    timestamp = db.Column(db.DateTime,
                           default=datetime.utcnow
    )

class User(db.Model):
     
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    username = db.Column(db.String(80), 
                          nullable = False, 
                          unique = True)

    email = db.Column(db.String(128),
                       nullable = False,
                       unique = True)

    password = db.Column(db.String(128),
                               nullable = False)

    #relationships to followers, posts, likes, comments
    posts = db.relationship('Post',
                             backref='author',
                             lazy=True)  #user's posts

    followed = db.relationship('Follower',
                                foreign_keys=[Follower.follower_id],
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic')    
     
    followers = db.relationship('Follower',
                                foreign_keys=[Follower.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic')  

    likes = db.relationship('Like',
                             backref='author',
                             lazy=True)

    comments = db.relationship('Comment',
                                backref='user',
                                lazy=True)  

    # instance methods:following/unfollowing users
    def is_following(self,user):
        return self.followed.filter_by(followed_id=user.id).count() > 0

    def follow(self, user):
        if not self.is_following(user):
            follow = Follower(follower_id=self.id, followed_id=user.id)
            db.session.add(follow)

    def unfollow(self, user):
        if self.is_following(user):
            Follower.query.filter_by(follower_id=self.id, followed_id=user.id).delete()

    # instance methods: liking and unlikeing posts
    def like_post(self, post):
        if not self.has_linked_post(post):
            like = Like(user_id=self.id, post_id=post.id)
            db.session.add(like)

    def has_liked_post(self, post):
        return Like.query.filter(Like.user_id==self.id, Like.post_id==post.id).count() > 0

    #for flask-login
    @property
    def is_active(self):
        return True  # all users in the database are considered authenticated

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False # user is not anonymous

    def get_id(self):
        """Return the user's ID as a string."""
        return str(self.id)  # Ensure that the ID is returned as a string

    #class method for signing up a new user
    @classmethod
    def signup(cls, username, email, password):
        """registers a new user.
            -hashes the password using Flask-Bcrypt and stores the user details in the database.
        """
        #hash the password with bycrpt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        #create new user object with hashed password
        new_user = cls(
            username=username,
            email=email,
            password=hashed_password
        )  

        #add the new user object with hashed password
        db.session.add(new_user)

        return new_user  

    #class method for authenicating users during login
    @classmethod
    def authenticate(cls, username, password):
        """auhenticate a user with username and password
            -finds the user by email and checks if the password matches using bcrypt
        """
        #find user by username
        print(f"authenticating user: {username}")
        user = cls.query.filter_by(username=username).first()

        #if user exists and password matches, return the user
        if user and bcrypt.check_password_hash(user.password, password):
            print(f"User {username} authenticaed successfully.")
            return user

        #otherwise, return none if authentication fails
        print("authentication failed")
        return None

class Post(db.Model):
    
    __tablename__ = 'posts'

    id = db.Column(db.Integer,
                    primary_key=True,
                    autoincrement=True)

    user_id = db.Column(db.Integer,
                         db.ForeignKey('users.id'),
                         nullable = False)

    spotify_id = db.Column(db.String(255), 
                            nullable=False)  

    spotify_name = db.Column(db.String(255), 
                              nullable=False)
    
    artist_name = db.Column(db.String(255), 
                            nullable=True)

    caption = db.Column(db.String(200), 
                         nullable=True)

    timestamp = db.Column(db.DateTime, 
                           default=datetime.utcnow)

    #relationships like and comments
    likes = db.relationship('Like',
                            backref='post',
                            cascade="all, delete-orphan",
                            lazy=True)

    comments = db.relationship('Comment',
                                backref='post',
                                cascade="all, delete-orphan", 
                                lazy=True)


class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, 
                    primary_key=True,
                    autoincrement=True)

    user_id = db.Column(db.Integer, 
                        db.ForeignKey('users.id'),
                        nullable=False)

    post_id = db.Column(db.Integer, 
                        db.ForeignKey('posts.id'),
                        nullable=False
    )
    

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, 
                    primary_key=True,
                    autoincrement=True)

    content = db.Column(db.Text, 
                        nullable=False)

    user_id = db.Column(db.Integer, 
                        db.ForeignKey('users.id'),
                        nullable=False)

    post_id = db.Column(db.Integer, 
                        db.ForeignKey('posts.id'),
                        nullable=False)



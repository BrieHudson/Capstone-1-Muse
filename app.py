import os 
import requests
import base64

from dotenv import load_dotenv
from flask import Flask, session, request, render_template, flash, redirect, url_for, g, current_app, jsonify
from flask_wtf import FlaskForm, CSRFProtect
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager, login_user, logout_user, current_user, login_required

from models import db, connect_db, User, Comment, Like, Follower, Post
from forms import PostForm, LoginForm, SignupForm, CommentForm, SearchForm

CURR_USER_KEY = "curr_user"

load_dotenv()

#Initialize Flask app and configuration
app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SUPABASE_DB_URL', 'postgresql:///muse_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True

app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
#app.config['DEBUG'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


connect_db(app)
toolbar = DebugToolbarExtension(app)

#Initialize extensions
login_manager = LoginManager(app)
login_manager.login_view = 'login' # redirect to login if user is not authenticated
csrf = CSRFProtect(app)



########################################################################################################

# Retrieves the user by their ID, Flask-login needs to maintain the user session across requests
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

"""Authentication routes"""

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

@app.route('/')
def root():
    """Redirect to the login page if user is not logged in."""
    if current_user.is_authenticated:  # check if there's a user in Flask's global object
        return redirect(url_for('feed'))  #redirect to the homepage if logged in 
    return redirect(url_for('login'))  #redirect to login if not authenticated

@app.route('/login', methods=['GET', 'POST'])
def login():
    """handle user login"""
    form = LoginForm()
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            login_user(user)
            print(f"Logged in user: {user.username}")
            
            if current_user.is_authenticated:
                print(f"Is authenticated: {current_user.is_authenticated}")
                return redirect(url_for('feed')) #redirect to user feed after login
            else:
                print("Login failed: User not authenticated")
        
        else:
            form.username.errors = ['Invalid username/password.']
            print("Login failed")
    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'] )
def signup():
    """handle user signup"""
    form = SignupForm()
    if form.validate_on_submit():
        #retrieve form data
        username = form.username.data
        email =  form.email.data
        password = form.password.data

        # Check if the username or email already exists
        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first() 
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('signup.html', form=form)
        if existing_email:
            flash('Email already registered. Please use a different email.', 'danger')
            return render_template('signup.html', form=form)

        # If everything is fine, create the new user
        user = User.signup(username=username,
                           email=email,
                           password=password)
        
        db.session.commit()  #save new user to the database

        login_user(user)  #login the user after signup

        flash('Account created successfully!', 'success')
        return redirect(url_for('feed'))

    return render_template('signup.html', form=form)
        

@app.route('/logout')
@login_required
def logout():
    """Logs user out and redirects to homepage."""
    logout_user()
    return redirect("/login")

#######################################################################################################


# Spotify API Client Credentials Flow #

def get_spotify_access_token():
    """Get an access token using Spotify's Client Credentials Flow"""

    auth_url = "https://accounts.spotify.com/api/token"

    headers ={
       'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'client_credentials',  # Required parameter
        'client_id': SPOTIFY_CLIENT_ID,      # Your Client ID
        'client_secret': SPOTIFY_CLIENT_SECRET # Your Client Secret
    }

    response = requests.post(auth_url, headers=headers, data=data)
    
    if response.status_code == 200:
        token_info = response.json()
        return token_info.get('access_token')
    else:
        print(f"Error getting Spotify token: {response.status_code}")
        return None

# Store spotify access token globally
spotify_access_token = get_spotify_access_token()
    
def search_spotify_api(query, search_type='track'):
    """Search for songs or playlists using the Spotify API."""
    global spotify_access_token
    
    # If the token expires, get a new one
    if not spotify_access_token:
        spotify_access_token = get_spotify_access_token()

    headers = {
        'Authorization': f'Bearer {spotify_access_token}'
    }
    params = {
        'q': query,
        'type': search_type,
        'limit': 10
    }

    response = requests.get('https://api.spotify.com/v1/search', headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error searching Spotify: {response.status_code}")
        return None


def get_spotify_item(spotify_id, item_type='track'):
    """Fetching the details of the selected song or playlist from Spotify API"""
    access_token = get_spotify_access_token()

    if item_type == 'track':
        url = f"https://api.spotify.com/v1/tracks/{spotify_id}"
    elif item_type == 'playlist':
        url = f"https://api.spotify.com/v1/playlists/{spotify_id}"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch item from Sotify API: {response.status_code}")

# Search Spotify route
@app.route('/search_spotify', methods=['GET'])
def search_spotify():
    """Return Spotify search results in real-time as the user types."""
    search_query = request.args.get('query', '')

    if not search_query:
        return jsonify({'error': 'No search query provided'}), 400

    # Spotify API request
    spotify_url = 'https://api.spotify.com/v1/search'

    headers = {
        'Authorization': f'Bearer {get_spotify_access_token()}'  # Ensure SPOTIFY_TOKEN is defined somewhere
    }

    params = {
        'q': search_query,
        'type': 'track,playlist',
        'limit': 5  # Limit to 5 results
    }

    response = requests.get(spotify_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()

        # Process Spotify API response for tracks and playlists
        tracks = [{'id': item['id'], 'name': item['name'], 'artist': item['artists'][0]['name']} for item in data.get('tracks', {}).get('items', [])]
        playlists = [{'id': item['id'], 'name': item['name']} for item in data.get('playlists', {}).get('items', [])]

        results = {'tracks': tracks, 'playlists': playlists}
        return jsonify(results)
    else:
        return jsonify({'error': 'Failed to fetch data from Spotify API'}), 500


######################################################################################################

"""User Routes"""

# profile page route
# profile following
# profile unfollowing


@app.route('/profile/<int:user_id>')
@login_required
def user_profile(user_id):
    """Display user profile with posts, followers, following, and likes"""
    user = User.query.get_or_404(user_id)
    
    # Get the user's posts
    user_posts = Post.query.filter_by(user_id=user_id).all()
    
    # Get liked posts by the user
    liked_posts = Post.query.join(Like, Like.post_id == Post.id).filter(Like.user_id == user_id).all()

    # Get followers and following counts
    followers_count = user.followers.count()
    following_count = user.followed.count()
    likes_count = len(liked_posts)  # Count liked posts

    return render_template('user_profile.html',
                           user=user,
                           user_posts=user_posts,
                           followers_count=followers_count,
                           following_count=following_count,
                           likes_count=likes_count,  # Pass likes count to the template
                           liked_posts=liked_posts)



# followers of current user
@app.route('/profile/<int:user_id>/followers')
@login_required
def user_followers(user_id):
    """ Show list of followers for the user"""
    user = User.query.get_or_404(user_id)
    followers = User.query.join(Follower, Follower.follower_id == User.id).filter(Follower.followed_id == user_id).all()

    return render_template('followers.html', user=user, followers=followers)

# following of current user
@app.route('/profile/<int:user_id>/following')
@login_required
def user_following(user_id):
    """Show list of people the user is following"""
    user = User.query.get_or_404(user_id)
    following = User.query.join(Follower, Follower.followed_id == User.id).filter(Follower.follower_id == user.id).all()

    return render_template('following.html', user=user, following=following)

# handle the following users of other users
@app.route('/follow/<int:user_id>', methods=["POST"])
@login_required
def follow_user(user_id):
    """Follow a user."""

    user_to_follow = User.query.get_or_404(user_id)

    if current_user.is_following(user_to_follow):
        flash(f'You are already following {user_to_follow.username}', 'warning')
    else:
        current_user.follow(user_to_follow)
        db.session.commit()
        flash(f'You are now following {user_to_follow.username}', 'success')

    return redirect(url_for('user_profile', user_id=user_id))

#handle unfollowing user of other users
@app.route('/unfollow/<int:user_id>', methods=["POST"])
@login_required
def unfollow_user(user_id):
    """Unfollow a user."""

    user_to_unfollow = User.query.get_or_404(user_id)

    if not current_user.is_following(user_to_unfollow):
        flash(f'You are not following {user_to_unfollow.username}', 'warning')
    else:
        current_user.unfollow(user_to_unfollow)
        db.session.commit()
        flash(f'You have unfollowed {user_to_unfollow.username}', 'success')

    return redirect(url_for('user_profile', user_id=user_id))

# current user likes
@app.route('/profile/<int:user_id>/likes')
@login_required
def user_likes(user_id):
    """Show all posts liked by the user"""
    user = User.query.get_or_404(user_id)
    
    # Get the liked posts
    liked_posts = Post.query.join(Like, Like.post_id == Post.id).filter(Like.user_id == user_id).all()

    return render_template('liked_posts.html', user=user, liked_posts=liked_posts)


####################################################################################

""" Post Routes """

@app.route('/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    """Allow the user to add a post with a song or playlist."""
    form = PostForm()
    if form.validate_on_submit():
        # Get the selected Spotify ID, name, and caption from the form
        selected_spotify_id = form.selected_spotify_id.data  # Hidden field with the selected Spotify item ID
        spotify_name = form.spotify_name.data  # Hidden field for the Spotify name
        artist_name = form.artist_name.data  # Get artist name if available
        post_caption = form.caption.data  # Caption from the form

        # Create a new Post instance in your database
        post = Post(
            user_id=current_user.id,
            spotify_id=selected_spotify_id,    # Store the Spotify ID of the selected item
            spotify_name=spotify_name,          # Store the song/playlist name
            artist_name=artist_name,
            caption=post_caption                 # Caption from the form
        )

        db.session.add(post)  # Add the new post to the session
        db.session.commit()   # Commit the session to save changes

        flash('Post added!', 'success')  # Flash a success message
        return redirect(url_for('feed'))  # Redirect to the feed or another page

    return render_template('add_post.html', form=form)  # Render the form if not submitted or invalid

# delete a post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    """Delete a post from the database."""
    print("Delete post route hit")
    post = Post.query.get_or_404(post_id)  # Retrieve the post by ID
    
   # Ensure that only the post's author can delete it
    if post.author != current_user:
        flash('You do not have permission to delete this post.', 'danger')
        return redirect(url_for('feed'))
    
    # remove associated likes and comment first
    Comment.query.filter_by(post_id=post.id).delete()
    Like.query.filter_by(post_id=post.id).delete()

    db.session.delete(post)  # Remove the post from the session
    db.session.commit()       # Commit the changes to the database

    flash('Post deleted!', 'success')  # Flash a success message
    return redirect(url_for('feed'))  # Redirect to the feed

# lika a post
@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    """Like a post."""
    post = Post.query.get_or_404(post_id)
    
    if not current_user.has_liked_post(post):
        like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(like)
        db.session.commit()
    
    return redirect(request.referrer or url_for('feed'))

# unlike a post
@app.route('/post/<int:post_id>/unlike', methods=['POST'])
@login_required
def unlike_post(post_id):
    """Unlike a post."""
    post = Post.query.get_or_404(post_id)
    
    if current_user.has_liked_post(post):
        Like.query.filter_by(user_id=current_user.id, post_id=post.id).delete()
        db.session.commit()

    return redirect(request.referrer or url_for('feed'))

# add comments
@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    """Add a comment to a post."""
    post = Post.query.get_or_404(post_id)
    form = CommentForm()

    comment_text = request.form.get('comment')

    if form.validate_on_submit():
        comment = Comment(content=form.content.data, user_id=current_user.id, post_id=post.id)
        
        db.session.add(comment)
        db.session.commit()

    return redirect(request.referrer or url_for('feed'))

#view comments
@app.route('/post/<int:post_id>/comments')
@login_required
def view_comments(post_id):
    """View all comments for a specific post."""
    post = Post.query.get_or_404(post_id)
    comments = post.comments
    return render_template('view_comments.html', post=post, comments=comments)

#####################################################################################

 #Fetch all post from users the current user is following, including their own posts

""" Feed Route """
@app.route('/feed')
@login_required
def feed():
    """Display posts from the current user and followed users"""

    # Retrieve the IDs of the followed users
    followed_user_ids = [f.followed_id for f in current_user.followed]

    # Create a query to fetch posts from followed users and the current user
    posts = Post.query.filter(
        (Post.user_id.in_(followed_user_ids)) | (Post.user_id == current_user.id)
    ).order_by(Post.timestamp.desc()).all()

    form = PostForm()
    return render_template('feed.html', posts=posts, form=form)




######################################################################################

""" Searching users routes"""
@app.route('/search', methods=['GET'])
@login_required
def search_users():
    query = request.args.get('query', '')  # Get the query from the URL parameters
    
    if query:  # Ensure the query is not empty
        results = User.query.filter(User.username.ilike(f'%{query}%')).all()
        return render_template('search_results.html', results=results, query=query)
    
    flash('Please enter a search term.', 'warning')  # Handle empty search
    return redirect(url_for('feed'))




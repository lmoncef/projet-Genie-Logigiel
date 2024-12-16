from flask import Flask, render_template, redirect, url_for, request, session

from datetime import datetime, timezone



from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    

class Post(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        content = db.Column(db.Text, nullable=False)
        timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Clé étrangère
        author = db.relationship('User', backref=db.backref('posts', lazy=True)) 

class FriendRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'accepted', 'declined'
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_requests')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_requests')

class Friend(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


     

# Routes
@app.route('/')
def index():
    if "user_id" in session:
        user_id = session['user_id']
        users = User.query.filter(User.id != user_id).all()  # Exclude the logged-in user
        received_requests = FriendRequest.query.filter_by(receiver_id=user_id, status='pending').all()
        posts = Post.query.order_by(Post.timestamp.desc()).all()
        return render_template('index.html', users=users, posts=posts, received_requests=received_requests)
    return redirect(url_for('login'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('index'))
        return "Invalid credentials!"
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            return "User already exists!"
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template("register.html")

@app.route('/logout')
def logout():
    session.pop("user_id", None)
    return redirect(url_for('login'))

@app.route('/post', methods=['POST'])
def post():
    if "user_id" not in session:
        return redirect(url_for("login"))
    content = request.form['content']
    new_post = Post(content=content, user_id=session['user_id'])
    db.session.add(new_post)
    db.session.commit()
    return redirect(url_for('index'))
@app.route('/post/delete/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    post = Post.query.get(post_id)
    if not post:
        return "Post not found!", 404

    if post.user_id != session['user_id']:
        return "Unauthorized!", 403

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/friend_request/send/<int:receiver_id>', methods=['POST'])
def send_friend_request(receiver_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    sender_id = session['user_id']
    if sender_id == receiver_id:
        return "You cannot send a friend request to yourself!", 400

    # Check if a friend request already exists
    existing_request = FriendRequest.query.filter_by(sender_id=sender_id, receiver_id=receiver_id).first()
    if existing_request:
        return "Friend request already sent!", 400

    # Create a new friend request
    friend_request = FriendRequest(sender_id=sender_id, receiver_id=receiver_id)
    db.session.add(friend_request)
    db.session.commit()
    return redirect(url_for('index'))
@app.route('/friend_request/accept/<int:request_id>', methods=['POST'])
def accept_friend_request(request_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    friend_request = FriendRequest.query.get(request_id)
    if not friend_request or friend_request.receiver_id != session['user_id']:
        return "Unauthorized!", 403

    friend_request.status = 'accepted'
    db.session.commit()
    return redirect(url_for('index'))
@app.route('/friend_request/decline/<int:request_id>', methods=['POST'])
def decline_friend_request(request_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    friend_request = FriendRequest.query.get(request_id)
    if not friend_request or friend_request.receiver_id != session['user_id']:
        return "Unauthorized!", 403

    db.session.delete(friend_request)
    db.session.commit()
    return redirect(url_for('index'))
@app.route('/friend_requests')
def view_friend_requests():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session['user_id']
    received_requests = FriendRequest.query.filter_by(receiver_id=user_id, status='pending').all()
    return render_template('friend_requests.html', requests=received_requests)



if __name__ == "__main__":
    with app.app_context():  # Activates the application context
        db.create_all()  # Creates database tables successfully
    app.run(debug=True)

from flask_migrate import Migrate

migrate = Migrate(app, db)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin@localhost/project'




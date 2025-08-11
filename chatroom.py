import flask, os, hashlib, sqlite3, time
app = flask.Flask(__name__)
app.secret_key = os.urandom(24)
DATABASE = 'app.db'
APP_START_TIME = time.time()

def get_db():
    db = getattr(flask.g, '_database', None)
    if db is None:
        db = flask.g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(flask.g, '_database', None)
    if db is not None:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                banned BOOLEAN DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')
        admin_username, admin_password_hash = 'ttrunf5', hash_password('1234')
        cursor.execute("SELECT id FROM users WHERE username = ?", (admin_username,))
        if not cursor.fetchone():
            print(f"Creating admin account: {admin_username}")
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (admin_username, admin_password_hash))
        db.commit()

# --- HTML Templates ---

LOGIN_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Chatroom Login</title><style>
body { font-family: Arial, sans-serif; background-color: #333; color: #fff; text-align: center; padding-top: 50px; }
.container { width: 350px; margin: 0 auto; background-color: #444; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.5); }
h2 { color: #00b0ff; }
input[type="text"], input[type="password"] { width: 90%; padding: 10px; margin: 10px 0; border: none; border-radius: 5px; }
.btn { width: 95%; padding: 10px; background-color: #00b0ff; color: #fff; border: none; border-radius: 5px; cursor: pointer; }
a { color: #00b0ff; text-decoration: none; display: block; margin-top: 15px; }
</style></head><body><div class="container"><h2>Chatroom Login</h2><form action="{{ url_for('login') }}" method="post"><input type="text" name="username" placeholder="Username" required><input type="password" name="password" placeholder="Password" required><button type="submit" class="btn">Log In</button></form><a href="{{ url_for('signup') }}">Don't have an account? Sign Up</a></div></body></html>"""

SIGNUP_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Chatroom Sign Up</title><style>
body { font-family: Arial, sans-serif; background-color: #333; color: #fff; text-align: center; padding-top: 50px; }
.container { width: 350px; margin: 0 auto; background-color: #444; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.5); }
h2 { color: #00b0ff; }
input[type="text"], input[type="password"] { width: 90%; padding: 10px; margin: 10px 0; border: none; border-radius: 5px; }
.btn { width: 95%; padding: 10px; background-color: #00b0ff; color: #fff; border: none; border-radius: 5-px; cursor: pointer; }
a { color: #00b0ff; text-decoration: none; display: block; margin-top: 15px; }
</style></head><body><div class="container"><h2>Chatroom Sign Up</h2><form action="{{ url_for('signup') }}" method="post"><input type="text" name="username" placeholder="Choose a Username" required><input type="password" name="password" placeholder="Choose a Password" required><button type="submit" class="btn">Sign Up</button></form><a href="{{ url_for('login') }}">Already have an account? Log In</a></div></body></html>"""

CHAT_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Simple Chatroom</title><style>
body { font-family: Arial, sans-serif; background-color: #333; color: #fff; padding-top: 20px; }
.container { width: 80%; max-width: 600px; margin: 0 auto; background-color: #444; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.5); min-height: 500px; display: flex; flex-direction: column; }
.chat-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.chat-header h2 { color: #00b0ff; margin: 0; }
.chat-window { flex-grow: 1; background-color: #555; padding: 10px; border-radius: 5px; text-align: left; overflow-y: auto; margin-bottom: 10px; }
.message { margin-bottom: 10px; }
.message .username { font-weight: bold; color: #00b0ff; margin-right: 5px; }
.message .text { word-wrap: break-word; }
form { display: flex; }
input[type="text"] { flex-grow: 1; padding: 10px; border: none; border-radius: 5px; margin-right: 10px; }
.btn { padding: 10px 20px; background-color: #00b0ff; color: #fff; border: none; border-radius: 5px; cursor: pointer; }
.btn-logout { background-color: #dc3545; padding: 10px 20px; border-radius: 5px; }
.btn:hover { background-color: #008fcc; }
/* NEW: Admin button style */
.btn-admin { 
    background-color: #6c757d; 
    color: #fff; 
    padding: 10px 15px; 
    border-radius: 5px;
    text-decoration: none;
    margin-right: 10px;
}
.btn-admin:hover { 
    background-color: #5a6268; 
}
</style></head><body><div class="container"><div class="chat-header"><h2>Welcome, {{ session['username'] }}!</h2><div>{% if session['username'] == 'ttrunf5' %}<a href="{{ url_for('admin_panel') }}" class="btn-admin">Admin Panel</a>{% endif %}<form action="{{ url_for('logout') }}" method="post" style="display:inline;"><button type="submit" class="btn btn-logout">Log Out</button></form></div></div><div class="chat-window" id="chat-window"></div><form id="message-form" onsubmit="sendMessage(); return false;"><input type="text" id="message-input" placeholder="Type your message..." required><button type="submit" class="btn">Send</button></form></div><script>
function fetchMessages(){fetch('/messages').then(response=>response.json()).then(data=>{const chatWindow=document.getElementById('chat-window');chatWindow.innerHTML='';data.forEach(msg=>{const messageDiv=document.createElement('div');messageDiv.className='message';messageDiv.innerHTML=`<span class="username">${msg.username}:</span><span class="text">${msg.text}</span>`;chatWindow.appendChild(messageDiv);});chatWindow.scrollTop=chatWindow.scrollHeight;});}
function sendMessage(){const message=document.getElementById('message-input').value;if(message){fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:message})}).then(()=>{document.getElementById('message-input').value='';fetchMessages();});}}
fetchMessages();setInterval(fetchMessages,3000);</script></body></html>"""

ADMIN_PANEL_PAGE = """
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Admin Panel</title><style>
body { font-family: Arial, sans-serif; background-color: #333; color: #fff; text-align: center; padding-top: 20px; }
.container { width: 80%; max-width: 800px; margin: 0 auto; background-color: #444; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.5); }
h2 { color: #00b0ff; }
.admin-section { text-align: left; margin-top: 20px; }
.admin-section h3 { color: #fff; border-bottom: 2px solid #00b0ff; padding-bottom: 5px; }
.admin-section form { margin-bottom: 15px; }
.admin-section input[type="text"], .admin-section input[type="password"] { padding: 8px; border-radius: 5px; border: none; margin-right: 5px; }
.btn { padding: 8px 12px; background-color: #00b0ff; color: #fff; border: none; border-radius: 5px; cursor: pointer; }
.btn-delete { background-color: #dc3545; }
.btn-delete:hover { background-color: #c82333; }
.btn-ban { background-color: #ffc107; color: #333; }
.btn-ban:hover { background-color: #e0a800; }
.stats-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
.stats-table th, .stats-table td { padding: 8px; border: 1px solid #555; }
.stats-table th { background-color: #555; }
.user-list, .message-list { list-style: none; padding: 0; }
.user-list li, .message-list li { margin-bottom: 5px; background-color: #555; padding: 5px; border-radius: 3px; }
a { color: #00b0ff; text-decoration: none; display: block; margin-top: 20px; }
.alert { color: #dc3545; font-weight: bold; }
</style></head><body><div class="container"><h2>Admin Panel</h2><p>Welcome, ttrunf5! Use the forms below to manage the chatroom.</p><a href="{{ url_for('home') }}">Back to Chatroom</a><div class="admin-section"><h3>Server Statistics</h3><p>Users: {{ stats['user_count'] }} | Messages: {{ stats['message_count'] }}</p><p>Current Uptime: {{ stats['uptime'] }}</p></div><div class="admin-section"><h3>Announce to Chat</h3><form action="{{ url_for('announce') }}" method="post"><input type="text" name="message" placeholder="System message..." required><button type="submit" class="btn">Announce</button></form></div><div class="admin-section"><h3>Chat Management</h3><form action="{{ url_for('clear_chat') }}" method="post" onsubmit="return confirm('Are you sure? This will delete all messages!');"><button type="submit" class="btn btn-delete">Delete All Messages</button></form><form action="{{ url_for('delete_message') }}" method="post"><input type="text" name="message_id" placeholder="Message ID" required><button type="submit" class="btn btn-delete">Delete by ID</button></form><form action="{{ url_for('clear_user_messages') }}" method="post"><input type="text" name="username" placeholder="Username" required><button type="submit" class="btn btn-delete">Clear User's Messages</button></form></div><div class="admin-section"><h3>User Management</h3><form action="{{ url_for('ban_user') }}" method="post"><input type="text" name="username" placeholder="Username to ban" required><button type="submit" class="btn btn-ban">Ban User</button></form><form action="{{ url_for('unban_user') }}" method="post"><input type="text" name="username" placeholder="Username to unban" required><button type="submit" class="btn">Unban User</button></form><form action="{{ url_for('change_password') }}" method="post"><input type="text" name="username" placeholder="Username" required><input type="password" name="new_password" placeholder="New Password" required><button type="submit" class="btn">Change Password</button></form><form action="{{ url_for('delete_user') }}" method="post" onsubmit="return confirm('Are you sure you want to delete this user? All their messages will be deleted too!');">
<input type="text" name="username" placeholder="Username to delete" required><button type="submit" class="btn btn-delete">Delete User</button></form><br><hr><h4>All Users</h4><ul class="user-list">{% for user in users %}<li>{{ user['username'] }} {% if user['banned'] %}<span class="alert">(BANNED)</span>{% endif %}</li>{% endfor %}</ul></div></div></body></html>"""

# --- Flask Routes ---
@app.route('/')
def home():
    if 'username' in flask.session:
        return flask.render_template_string(CHAT_PAGE)
    return flask.redirect(flask.url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        db = get_db()
        user_row = db.execute("SELECT password_hash, banned FROM users WHERE username = ?", (flask.request.form['username'],)).fetchone()
        if user_row and user_row['password_hash'] == hash_password(flask.request.form['password']):
            if user_row['banned']:
                return flask.render_template_string(LOGIN_PAGE)
            flask.session['username'] = flask.request.form['username']
            return flask.redirect(flask.url_for('home'))
    return flask.render_template_string(LOGIN_PAGE)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if flask.request.method == 'POST':
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (flask.request.form['username'], hash_password(flask.request.form['password'])))
            db.commit()
            flask.session['username'] = flask.request.form['username']
            return flask.redirect(flask.url_for('home'))
        except sqlite3.IntegrityError:
            return flask.render_template_string(SIGNUP_PAGE)
    return flask.render_template_string(SIGNUP_PAGE)

@app.route('/logout', methods=['POST'])
def logout():
    flask.session.pop('username', None)
    return flask.redirect(flask.url_for('login'))

@app.route('/admin_panel')
def admin_panel():
    if flask.session.get('username') == 'ttrunf5':
        db = get_db()
        stats = {'user_count': db.execute("SELECT COUNT(*) FROM users").fetchone()[0], 'message_count': db.execute("SELECT COUNT(*) FROM messages").fetchone()[0], 'uptime': f"{int(time.time() - APP_START_TIME)} seconds"}
        users = db.execute("SELECT username, banned FROM users").fetchall()
        return flask.render_template_string(ADMIN_PANEL_PAGE, stats=stats, users=users)
    return flask.redirect(flask.url_for('home'))

@app.route('/admin/announce', methods=['POST'])
def announce():
    if flask.session.get('username') == 'ttrunf5':
        message = flask.request.form.get('message')
        if message:
            db = get_db()
            db.execute("INSERT INTO messages (username, text, timestamp) VALUES (?, ?, ?)", ("System", message, time.time()))
            db.commit()
    return flask.redirect(flask.url_for('admin_panel'))

@app.route('/admin/clear_chat', methods=['POST'])
def clear_chat():
    if flask.session.get('username') == 'ttrunf5':
        db = get_db()
        db.execute("DELETE FROM messages")
        db.commit()
    return flask.redirect(flask.url_for('admin_panel'))
    
@app.route('/admin/delete_message', methods=['POST'])
def delete_message():
    if flask.session.get('username') == 'ttrunf5':
        message_id = flask.request.form.get('message_id')
        db = get_db()
        db.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        db.commit()
    return flask.redirect(flask.url_for('admin_panel'))

@app.route('/admin/clear_user_messages', methods=['POST'])
def clear_user_messages():
    if flask.session.get('username') == 'ttrunf5':
        username_to_clear = flask.request.form.get('username')
        db = get_db()
        db.execute("DELETE FROM messages WHERE username = ?", (username_to_clear,))
        db.commit()
    return flask.redirect(flask.url_for('admin_panel'))

@app.route('/admin/ban_user', methods=['POST'])
def ban_user():
    if flask.session.get('username') == 'ttrunf5':
        username_to_ban = flask.request.form.get('username')
        db = get_db()
        db.execute("UPDATE users SET banned = 1 WHERE username = ?", (username_to_ban,))
        db.commit()
    return flask.redirect(flask.url_for('admin_panel'))
    
@app.route('/admin/unban_user', methods=['POST'])
def unban_user():
    if flask.session.get('username') == 'ttrunf5':
        username_to_unban = flask.request.form.get('username')
        db = get_db()
        db.execute("UPDATE users SET banned = 0 WHERE username = ?", (username_to_unban,))
        db.commit()
    return flask.redirect(flask.url_for('admin_panel'))

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    if flask.session.get('username') == 'ttrunf5':
        username = flask.request.form.get('username')
        new_password = flask.request.form.get('new_password')
        db = get_db()
        db.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_password(new_password), username))
        db.commit()
    return flask.redirect(flask.url_for('admin_panel'))

@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    if flask.session.get('username') == 'ttrunf5':
        username_to_delete = flask.request.form.get('username')
        db = get_db()
        db.execute("DELETE FROM users WHERE username = ?", (username_to_delete,))
        db.execute("DELETE FROM messages WHERE username = ?", (username_to_delete,))
        db.commit()
    return flask.redirect(flask.url_for('admin_panel'))
    
@app.route('/messages')
def get_messages():
    db = get_db()
    messages = db.execute("SELECT id, username, text FROM messages ORDER BY timestamp").fetchall()
    return flask.jsonify([dict(row) for row in messages])

@app.route('/send', methods=['POST'])
def send_message():
    if 'username' not in flask.session:
        return flask.jsonify({'status': 'error', 'message': 'Not logged in'}), 401
    data = flask.request.json
    if data and 'text' in data:
        db = get_db()
        db.execute("INSERT INTO messages (username, text, timestamp) VALUES (?, ?, ?)", (flask.session['username'], data['text'], time.time()))
        db.commit()
        return flask.jsonify({'status': 'success'})
    return flask.jsonify({'status': 'error', 'message': 'Invalid data'}), 400

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

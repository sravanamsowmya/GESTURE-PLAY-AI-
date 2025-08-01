# app.py

from flask import Flask, render_template, request, redirect, url_for, session
from auth import validate_user, register_user
import os
import subprocess
import sys

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if validate_user(email, password):
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Invalid email or password.")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if register_user(email, password):
            session['user'] = email
            return redirect(url_for('dashboard'))
        else:
            return render_template('signup.html', error="Email already exists.")
    return render_template('signup.html')

@app.route('/dashboard')
def dashboard():
    if 'user' in session:
        return render_template('dashboard.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# New Pages
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/demo')
def demo():
    return render_template('demo.html')

@app.route('/technologies')
def technologies():
    return render_template('technologies.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

# Play Game Route
@app.route('/play/<game>')
def play_game(game):
    if 'user' not in session:
        return redirect(url_for('login'))

    script_map = {
        'rps': 'gesture_rps.py',
        'tictactoe': 'gesture_tictactoe.py',
        '2048': 'gesture_2048.py'
    }

    if game not in script_map:
        return "Invalid game selected."

    script_path = os.path.join(os.getcwd(), script_map[game])

    try:
        subprocess.Popen(
            [sys.executable, script_path],
            creationflags=subprocess.CREATE_NEW_CONSOLE  # Only works on Windows
        )
    except Exception as e:
        return f"Failed to launch game: {e}"

    return f"<h2>Launching {game.capitalize()} game...<br>Close the game window to return.</h2>"
if __name__ == '__main__':
    app.run(debug=True)

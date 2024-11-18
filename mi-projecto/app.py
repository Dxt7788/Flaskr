from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, send
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# Configuración de la app
app = Flask(__name__)
app.secret_key = os.getenv("MCPE1234")

# Inicializamos Flask-SocketIO
socketio = SocketIO(app)

# Conexión a la base de datos MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("localhost"),
        user=os.getenv("Daniel"),
        password=os.getenv("MCPE1234"),
        database=os.getenv("db")
    )
    return conn

# Página de inicio (login)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):  # user[2] es el campo 'password'
            session['username'] = user[1]  # Guardamos el username en la sesión
            return redirect(url_for('chat'))  # Redirigimos al chat
        else:
            flash('Credenciales incorrectas. Intenta de nuevo.', 'error')
    
    return render_template('login.html')

# Página de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user:
            flash('El nombre de usuario ya existe.', 'error')
        else:
            cursor.execute('INSERT INTO usuarios (username, password) VALUES (%s, %s)', (username, password_hash))
            conn.commit()
            flash('Registro exitoso. Inicia sesión.', 'success')
            return redirect(url_for('login'))

        conn.close()

    return render_template('register.html')

# Página del chat (requiere estar logueado)
@app.route('/chat')
def chat():
    if 'username' not in session:
        return redirect(url_for('login'))  # Si no está logueado, redirige al login
    
    return render_template('chat.html', username=session['username'])

# Maneja los mensajes del chat
@socketio.on('message')
def handle_message(msg):
    username = session.get('username', 'Anonimo')  # Obtenemos el usuario actual
    full_message = f"{username}: {msg}"  # Incluimos el usuario en el mensaje
    send(full_message, broadcast=True)  # Envía el mensaje a todos los clientes conectados

# Ejecuta la aplicación con SocketIO
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

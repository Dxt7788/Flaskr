from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_socketio import SocketIO, send
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import os
from flask_cors import CORS  # Para habilitar CORS si es necesario

# Configuración de la app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'MCPE1234')  # Cambia esto por algo más seguro en producción

# Habilitar CORS (si es necesario)
CORS(app)

# Inicializamos Flask-SocketIO
socketio = SocketIO(app)

# Conexión a la base de datos MySQL
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),  # Usa variables de entorno para configuraciones de Render
        user=os.getenv('DB_USER', 'Daniel'),
        password=os.getenv('DB_PASSWORD', 'MCPE1234'),
        database=os.getenv('DB_NAME', 'db')
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
    username = session.get('username', 'Anónimo')
    print(f'Recibido de {username}: {msg}')
    send(f'{username}: {msg}', broadcast=True)  # Envía el mensaje a todos los clientes conectados

# Ejecuta la aplicación con SocketIO
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)

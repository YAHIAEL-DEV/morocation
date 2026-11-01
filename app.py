from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import re
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'votre_cle_secrete_ici_changez_la')
# ===== CONFIG UPLOAD =====
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ===== CONFIG EMAIL (BADAL HNA B CREDENTIALS DIALK) =====
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'tonemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'tonmotdepasseapp'
app.config['MAIL_DEFAULT_SENDER'] = 'tonemail@gmail.com'
mail = Mail(app)

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'morocation')
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Erreur MySQL: {e}")
        return None

def init_db():
    try:
        config = DB_CONFIG.copy()
        config.pop('database', None)
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS morocation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
        cursor.close()
        conn.close()

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nom VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                avatar VARCHAR(255) DEFAULT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("Base de donnees initialisee avec succes!")
    except Error as e:
        print(f"Erreur: {e}")

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Email et mot de passe requis", "error")
            return render_template('login.html')

        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            flash("Email invalide", "error")
            return render_template('login.html')

        conn = get_db_connection()
        if not conn:
            flash("Erreur de connexion", "error")
            return render_template('login.html')

        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                session['user_nom'] = user['nom']
                if user.get('avatar'):
                    session['user_avatar'] = user['avatar']
                flash(f"Bienvenue {user['nom']} !", "success")
                return redirect(url_for('main'))
            else:
                flash("Email ou mot de passe incorrect", "error")
        except Error as e:
            flash(f"Erreur: {str(e)}", "error")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not nom or not email or not password:
            flash("Tous les champs sont requis", "error")
            return render_template('register.html')

        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas", "error")
            return render_template('register.html')

        if len(password) < 6:
            flash("Min 6 caracteres", "error")
            return render_template('register.html')

        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            flash("Email invalide", "error")
            return render_template('register.html')

        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        if not conn:
            flash("Erreur de connexion", "error")
            return render_template('register.html')

        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (nom, email, password_hash) VALUES (%s, %s, %s)",
                (nom, email, password_hash))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Compte cree avec succes!", "success")
            return redirect(url_for('login'))
        except Error as e:
            if "Duplicate entry" in str(e):
                flash("Cet email est deja utilise", "error")
            else:
                flash(f"Erreur: {str(e)}", "error")

    return render_template('register.html')

@app.route('/main')
def main():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('main.html', user=session)

@app.route('/favorites')
def favorites():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('8Favorites.html', user=session)

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('7Profile.html', user=session)

@app.route('/reservations')
def reservations():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('9Reservation.html', user=session)

@app.route('/search')
def search():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('6Search.html', user=session)

@app.route('/hotels')
def hotels():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('Hotels.html', user=session)

@app.route('/restaurants')
def restaurants():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('Restaurants.html', user=session)

@app.route('/voir-tout')
def voir_tout():
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('VoirTout.html', user=session)

@app.route('/destination/<name>')
def destination(name):
    if 'user_id' not in session:
        flash("Veuillez vous connecter", "error")
        return redirect(url_for('login'))
    return render_template('5Destination Detail.html', user=session, name=name)

@app.route('/logout')
def logout():
    session.clear()
    flash("Deconnecte avec succes", "success")
    return redirect(url_for('login'))

# ============================================
# ===== API: UPDATE PROFILE (NOM + AVATAR) =====
# ============================================
@app.route('/api/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non connecte'}), 401
    
    user_id = session['user_id']
    nom = request.form.get('nom', '').strip()
    
    if not nom:
        return jsonify({'success': False, 'message': 'Nom requis'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur BDD'})
    
    try:
        cursor = conn.cursor()
        avatar_url = None
        
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and allowed_file(file.filename):
                filename = secure_filename(f"user_{user_id}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                avatar_url = f"/{filepath.replace(os.sep, '/')}"
                cursor.execute("UPDATE users SET avatar = %s WHERE id = %s", (avatar_url, user_id))
        
        cursor.execute("UPDATE users SET nom = %s WHERE id = %s", (nom, user_id))
        conn.commit()
        
        session['user_nom'] = nom
        if avatar_url:
            session['user_avatar'] = avatar_url
        
        return jsonify({
            'success': True,
            'message': 'Profil mis a jour',
            'avatar_url': avatar_url
        })
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== API: CHANGE PASSWORD =====
# ============================================
@app.route('/api/change-password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non connecte'}), 401
    
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'message': 'Tous les champs requis'})
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'Min. 6 caracteres'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Erreur BDD'})
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
        
        if not user or not check_password_hash(user['password_hash'], old_password):
            return jsonify({'success': False, 'message': 'Mot de passe actuel incorrect'})
        
        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = %s WHERE id = %s", 
                      (new_hash, session['user_id']))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Mot de passe change'})
        
    except Error as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

# ============================================
# ===== API: RESERVATION + EMAIL =====
# ============================================
@app.route('/api/reserve', methods=['POST'])
def reserve():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Non connecte'}), 401
    
    data = request.get_json()
    user_email = session.get('user_email')
    user_nom = session.get('user_nom')
    
    try:
        msg = Message(
            'Confirmation de reservation - MoroCation',
            sender=app.config['MAIL_DEFAULT_SENDER'],
            recipients=[user_email]
        )
        msg.body = f"""
Bonjour {user_nom},

Votre reservation a ete confirmee avec succes !

Details:
- Hotel: {data.get('hotel_name')}
- Lieu: {data.get('hotel_location')}
- Arrivee: {data.get('checkin')}
- Depart: {data.get('checkout')}
- Nuits: {data.get('nights')}
- Personnes: {data.get('guests')}
- Total: {data.get('total')}
- Paiement: {data.get('payment_method', 'Carte').upper()}

Merci d'avoir choisi MoroCation !
"""
        msg.html = f"""
<h2 style="color:#10b981;">Confirmation de reservation - MoroCation</h2>
<p>Bonjour <strong>{user_nom}</strong>,</p>
<p>Votre reservation a ete <strong style="color:#10b981;">confirmee</strong> avec succes !</p>
<table style="border-collapse:collapse;width:100%;max-width:500px;">
    <tr style="background:#f8fafc;"><td style="padding:10px;border:1px solid #e5e7eb;font-weight:600;">Hotel</td><td style="padding:10px;border:1px solid #e5e7eb;">{data.get('hotel_name')}</td></tr>
    <tr><td style="padding:10px;border:1px solid #e5e7eb;font-weight:600;">Lieu</td><td style="padding:10px;border:1px solid #e5e7eb;">{data.get('hotel_location')}</td></tr>
    <tr style="background:#f8fafc;"><td style="padding:10px;border:1px solid #e5e7eb;font-weight:600;">Arrivee</td><td style="padding:10px;border:1px solid #e5e7eb;">{data.get('checkin')}</td></tr>
    <tr><td style="padding:10px;border:1px solid #e5e7eb;font-weight:600;">Depart</td><td style="padding:10px;border:1px solid #e5e7eb;">{data.get('checkout')}</td></tr>
    <tr style="background:#f8fafc;"><td style="padding:10px;border:1px solid #e5e7eb;font-weight:600;">Nuits</td><td style="padding:10px;border:1px solid #e5e7eb;">{data.get('nights')}</td></tr>
    <tr><td style="padding:10px;border:1px solid #e5e7eb;font-weight:600;">Personnes</td><td style="padding:10px;border:1px solid #e5e7eb;">{data.get('guests')}</td></tr>
    <tr style="background:#ecfdf5;"><td style="padding:10px;border:1px solid #e5e7eb;font-weight:600;">Total</td><td style="padding:10px;border:1px solid #e5e7eb;color:#10b981;font-weight:bold;font-size:18px;">{data.get('total')}</td></tr>
</table>
<p style="margin-top:20px;color:#6b7280;">Merci d'avoir choisi <strong>MoroCation</strong> !</p>
"""
        mail.send(msg)
        
        return jsonify({'success': True, 'message': 'Reservation confirmee, email envoye'})
        
    except Exception as e:
        print(f"Erreur email: {e}")
        return jsonify({'success': True, 'message': 'Reservation confirmee, email non envoye'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
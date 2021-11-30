import re
import sqlite3, random
from flask import Flask, render_template, jsonify, request, url_for, flash, redirect, session
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
cmd_queue = []

@app.route('/registrar', methods=['POST', 'GET'])
def registrar():
    if request.method == "POST":
        username = request.form["username"]
        user_email = request.form["user_email"]
        passwd_src = request.form["passwd_src"]
        passwd_ver = request.form["passwd_ver"]
        if passwd_src == passwd_ver:
            db_con = sqlite3.connect('seedhub_db')
            db_cur = db_con.cursor()
            user = {}
            user["id"] = random.getrandbits(32)
            user["username"] = username
            user["email"] = user_email
            user["password"] = passwd_src
            try:
                db_cur.execute("INSERT INTO users values (:id, :username, :email, :password)", user)
                db_con.commit()
            except sqlite3.IntegrityError:
                flash("Username or email already registered")
                return redirect(url_for('registrar'))
            finally:
                db_con.close()
            flash("Successfully registered {user}".format(user=username))
            return redirect(url_for('registrar'))
        else:
            flash("Passwords do not match")
            return redirect(url_for('registrar'))
    else:    
        return render_template('Registrar.html')

@app.route('/login', methods=["POST", "GET"]) 
def login():
    if request.method == "POST":
        user = {}
        user["username"] = request.form["username"]
        user["password"] = request.form["password"]
        db_con = sqlite3.connect('seedhub_db')
        db_cur = db_con.cursor()
        try:
            db_cur.execute("SELECT * FROM users WHERE username=:username AND password=:password", user)
            user = db_cur.fetchall()
            if len(user) == 1:
                session["u_id"] = user[0][0]
                session["user"] = user[0][1]
                session["email"] = user[0][2]
                print(session)
                return redirect(url_for('index'))
            else:
                flash("Bad log in information")
                return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username or email already used")
            return redirect(url_for('login'))
        finally:
            db_con.close()
    return render_template('Login.html')

@app.route('/miperfil')  
def miperfil():
    return render_template('MiPerfil.html')

@app.route('/misplantas')  
def misplantas():
    return render_template('InfoUsuario.html')

@app.route('/estadistica')  
def estadistica():
    return render_template('Estadistica.html')    

@app.route('/')
def index():
    if session.get("u_id"):
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/api/hello')
def hello():
    return jsonify({"message":"Hello, world"})

@app.route('/api/save_info', methods=['POST'])
def save_info():
    plant_info = request.get_json()
    print(plant_info)
    return jsonify(plant_info)

@app.route('/serial/toggle_leds')
def toggle_leds():
    cmd_queue.append('<toggle_leds,0>')
    return jsonify("OK")

@app.route('/serial/get_cmd')
def get_command():
    cmd = None
    try:
        cmd = cmd_queue.pop(0)
    except:
        cmd = "None"
    return jsonify({"cmd":cmd})

if __name__ == "__main__":
    app.run(debug=True)

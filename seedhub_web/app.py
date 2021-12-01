import server
import sqlite3, random
from sqlite3.dbapi2 import connect
from flask_socketio import SocketIO
from flask_serial import Serial
from flask import Flask, render_template, jsonify, request, url_for, flash, redirect, session

app = Flask(__name__)
app.config['SERIAL_TIMEOUT'] = 0.3
app.config['SERIAL_PORT'] = 'ttyUSB0'
app.config['SERIAL_BAUDRATE'] = 9600
app.config['SERIAL_BYTESIZE'] = 8
app.config['SERIAL_PARITY'] = 'N'
app.config['SERIAL_STOPBITS'] = 1
app.config['SECRET_KEY'] = 'mysecretkey'
cmd_queue = []

def add_plant(plant_src):
    if plant_src == None:
        return
    db_con = sqlite3.connect('seedhub_db')
    db_cur = db_con.cursor()
    plant_src["p_id"] = random.getrandbits(32)
    plant_src["u_id"] = session["u_id"]
    plant_src['c_id'] = random.getrandbits(32)
    try:
        db_cur.execute("INSERT INTO plants values (:p_id, :name, :type, :desc, :u_id)", plant_src)
        db_cur.execute("INSERT INTO plant_conf(id, p_id) values(:c_id, :p_id)", plant_src)
        db_con.commit()
        return True
    except:
        return False
    finally:
        db_con.close()

def update_plant(plant_src):
    if not plant_src:
        return
    db_con = sqlite3.connect('seedhub_db')
    db_cur = db_con.cursor()
    try:    
        #db_cur.execute("UPDATE plants SET name=:name, type=:type, desc=:desc, u_id=:u_id WHERE id=:id", plant_src)
        plant_conf = plant_src["conf"]
        db_cur.execute("UPDATE plant_conf SET soil_moist=:soil_moist, led_hours=:led_hours, led_dimming=:led_dimming, fans_cycle=:fans_cycle, fans_runtime=:fans_runtime, pump_runtime=:pump_runtime, checkup_time=:checkup_time WHERE id=:id ", plant_conf)
        db_con.commit()
        return True
    except sqlite3.Error as e:
        print(e)
        return False
    finally:
        db_con.close()
    
def get_plants():
    db_con = sqlite3.connect('seedhub_db')
    db_cur = db_con.cursor()
    try:
        db_cur.execute("SELECT * FROM plants WHERE u_id=:id", {"id":session["u_id"]})
        records = db_cur.fetchall()
        if len(records) > 0:
            plants = []
            for record in records:
                plant = {}
                plant["id"] = record[0]
                plant["name"] = record[1]
                plant["type"] = record[2]
                plant["desc"] = record[3]
                plants.append(plant)
            return plants
        return []
    except:
        pass
    finally:
        db_con.close()

def get_plant_by_id(p_id):
    db_con = sqlite3.connect('seedhub_db')
    db_cur = db_con.cursor()
    try:
        db_cur.execute("SELECT * FROM plants WHERE id=:p_id", {"p_id":p_id})
        records = db_cur.fetchall()
        if len(records) > 0:
            plant = {}
            for record in records:
                plant["id"] = record[0]
                plant["name"] = record[1]
                plant["type"] = record[2]
                plant["desc"] = record[3]
            return plant
        return {}
    except:
        pass
    finally:
        db_con.close()

def get_plant_config(p_id):
    db_con = sqlite3.connect('seedhub_db')
    db_cur = db_con.cursor()
    try:
        db_cur.execute("SELECT * FROM plant_conf WHERE p_id=:id", {"id":p_id})
        records = db_cur.fetchall()
        conf = {}
        if len(records) > 0:
            for record in records:
                conf["id"] = record[0]
                conf["soil_moist"] = record[1]
                conf["led_bright"] = record[2]
                conf["led_houts"] = record[3]
                conf["led_dimming"] = record[4]
                conf["fans_cycle"] = record[5]
                conf["fans_runtime"] = record[6]
                conf["pump_runtime"] = record[7]
                conf["checkup_time"] = record[8]
                conf["p_id"] = record[9]
            return conf
        else:
            conf["id"] = random.getrandbits(32)
            return conf
    except sqlite3.Error as e:
        print(e)
        pass
    finally:
        db_con.close()

@app.route('/connect_arduino')
def connect_to_arduino(methods=['POST','GET']):
    if request.method == "GET":
        plant_id = str(request.args.get('link_plant'))
        print(plant_id)
        server.start(plant_id)

@app.route('/log_out', methods=['POST'])
def log_out():
    if request.method == "POST":
        session.clear()
    return redirect(url_for('index'))

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
    if "u_id" in session:
        return render_template('MiPerfil.html')
    return redirect(url_for('index'))

@app.route('/edit_plant', methods=['POST'])
def edit_plant():
    if request.method == "POST":
        plant = {}
        if "edit_plant" in request.form:
            plant["id"] = request.form["edit_plant"]
            plant["name"] = request.form["plant_name"]
            plant["type"] = request.form["plant_type"]
            plant["desc"] = request.form["plant_desc"]
            plant["u_id"] = session["u_id"]
            conf = {}
            conf["id"] = request.form["conf_id"]
            conf["soil_moist"] = request.form["soil_moist"]
            conf["led_bright"] = request.form["led_bright"]
            conf["led_hours"] = request.form["led_hours"]
            conf["led_dimming"] = 1 if request.form["led_dimming"] == "True" else 0
            conf["fans_cycle"] = request.form["fans_cycle"]
            conf["fans_runtime"] = request.form["fans_runtime"]
            conf["checkup_time"] = request.form["pump_cycle_time"]
            conf["pump_runtime"] = request.form["pump_time"]
            conf["p_id"] = plant["id"]
            plant["conf"] = conf
            if update_plant(plant):
                flash("Sucessfully updated plant {name}".format(name=plant["name"]), category="alert-success")
            else:
                flash("Error updating plant {name}".format(name=plant["name"]), category="alert-warning")
        elif "plant_id" in request.form:
            plant["id"] = request.form["plant_id"]
        plant = get_plant_by_id(plant["id"])
        plant["conf"] = get_plant_config(plant["id"])
        return render_template('edit_plant.html', plant=plant);
    return redirect(url_for('index'))

@app.route('/misplantas', methods=['POST', 'GET'])  
def misplantas():
    if "u_id" in session:
        if request.method == "POST":
            if "add_plant" in request.form:
                plant = {}
                plant["name"] = request.form["plant_name"]
                plant["type"] = request.form["plant_type"]
                plant["desc"] = request.form["plant_desc"]
                if add_plant(plant):
                    flash("Sucessfully added plant {name}".format(name=plant["name"]), category="alert-success")
                else:
                    flash("Error adding plant {name}".format(name=plant["name"]), category="alert-warning")
        plants = get_plants()
        return render_template('MisPlantas.html', plants=plants)
    return redirect(url_for('login'))

@app.route('/estadistica')  
def estadistica():
    if "u_id" in session:
        return render_template('Estadistica.html')
    return redirect(url_for('index'))

@app.route('/contacto')
def contacto():
    if "u_id" in session:
        return render_template('Contacto.html')
    return redirect(url_for('index'))

@app.route('/')
def index():
    if "u_id" in session:
        return redirect(url_for('misplantas'))
    else:
        return redirect(url_for('login'))

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

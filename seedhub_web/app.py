from flask import Flask, render_template, jsonify, request

app = Flask(__name__)
cmd_queue = []


@app.route('/registrar')
def registrar():    
    return render_template('Registrar.html')
@app.route('/login')  
def login1():
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
    return render_template('index.html')

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

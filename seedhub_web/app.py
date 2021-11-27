import re
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/registrar')
def registrar():    
    return render_template('Registrar.html')

@app.route('/')  
def login():
    return render_template('Login.html')
if __name__ == "__main__":
    app.run(debug=True)

@app.route('/miperfil')  
def miperfil():
    return render_template('MiPerfil.html')

@app.route('/infousuario')  
def infousuarito():
    return render_template('InfoUsuario.html')

@app.route('/estadistica')  
def estadistica():
    return render_template('Estadistica.html')    

@app.route('/index')  
def index():
    return render_template('index.html')    
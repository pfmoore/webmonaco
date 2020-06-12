from flask import Flask, request
import subprocess
from pathlib import Path

app = Flask(__name__)
monaco = Path(__file__).parent / "bin/monaco.exe"

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/monaco', methods=['GET', 'POST']) #allow both GET and POST requests
def form_example():
    if request.method == 'POST':  #this block is only entered when the form is submitted
        command = request.form.get('command')

        if command:
            p = subprocess.run(f"{monaco} {command}", shell=True, capture_output=True, text=True)
            return f'''<h1>Command: {command}</h1>
            Return code: {p.returncode}<br>
            <pre>
            {p.stdout}
            </pre>
        '''
        else:
            return '''No command given'''

    return '''<form method="POST">
                  Command: <input type="text" name="command"><br>
                  <input type="submit" value="Submit"><br>
              </form>'''

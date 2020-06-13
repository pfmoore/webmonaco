from flask import Flask, request
import subprocess
from pathlib import Path
import sys

app = Flask(__name__)

monaco_bin = (Path(__file__).parent / "bin" / sys.platform / "monaco").absolute()
page = (Path(__file__).parent / "html/index.html").absolute()

@app.route('/', methods=['GET', 'POST'])
def monaco():
    if request.method == "POST":
        return show_results(request)
    return page.read_text()

def show_results(request):
    if request.method == 'POST':  #this block is only entered when the form is submitted
        expr = request.form.get('expr')
        statistics = bool(request.form.get("statistics"))
        histogram = bool(request.form.get("histogram"))
        exact = bool(request.form.get("exact"))
        iterations = int(request.form.get("iterations"))

        command = [str(monaco_bin)]
        if statistics:
            command.append("-statistics")
        if histogram:
            command.append("-histogram")
        if exact:
            command.append("-exact")
        command.append(expr)
        command.append(str(iterations))
        print(command)
        p = subprocess.run(command, capture_output=True, text=True)
        return f'''<h1>Command: {command}</h1>
        Return code: {p.returncode}<br>
        <pre>
        {p.stdout}
        </pre>
        '''

if __name__ == "__main__":
    app.run(threaded=True, port=5000)
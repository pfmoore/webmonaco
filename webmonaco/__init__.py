from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
from pathlib import Path
import sys
import os
import stat
import shlex
import traceback
import tempfile


monaco_bin = (Path(__file__).parent / f"bin/{sys.platform}/monaco").absolute()
if sys.platform == "linux":
    st = os.stat(monaco_bin)
    os.chmod(monaco_bin, st.st_mode | stat.S_IEXEC)


app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        return show_results(request)
    return render_template("index.html")

@app.route("/run", methods=['GET', 'POST'])
def test():
    if request.method == "GET":
        commands = []
        for option_set in request.args.getlist("option"):
            commands.append(option_set)
        if "expr" in request.args:
            commands.append("$" + request.args["expr"])
        if "number" in request.args:
            commands.append("$" + request.args["number"])
        file_content = "\n".join(commands)
    elif not request.is_json:
        file_content = request.get_data(as_text=True)
    else:
        data = request.get_json()
        commands = []
        for option_set in data.get("options", []):
            commands.append(option_set)
        if "expr" in data:
            commands.append("$" + data["expr"])
        if "number" in data:
            commands.append("$" + data["number"])
        file_content = "\n".join(commands)

    with tempfile.TemporaryDirectory() as d:
        cmdfile = Path(d) / "monaco.data"
        with cmdfile.open("w") as f:
            # Suppress "press enter" pause...
            print("-noprompt", file=f)
            print(file_content, file=f)
        command = [str(monaco_bin), cmdfile.name]
        proc = subprocess.run(command, capture_output=True, encoding="utf-8", cwd=d)

        return {"returncode": proc.returncode, "stdout": proc.stdout}

@app.route("/monaco")
def monaco():
    command = [str(monaco_bin)] + parse_options(request.args)
    proc = subprocess.run(command, stdout=subprocess.PIPE, encoding="utf-8")
    return jsonify(dict(stdout=proc.stdout))


CHECKBOXES = [
    "statistics",
    "histogram",
    "cumulative",
    "rcumulative",
    "percent",
    "probability",
    "exact",
    "new",
]
def parse_options(args):
    options = []
    from pprint import pprint
    pprint(args)
    for checkbox in CHECKBOXES:
        if args.get(checkbox):
            options.append("-" + checkbox)

    other_options = args.get("other_options")
    if other_options:
        # Note: shlex.split is awful, it reads stdin if
        # you pass None as input. Avoid that or the webapp
        # will hang!
        other_options = shlex.split(other_options)
        options.extend(other_options)

    expr = args.get('expr')
    # Monaco doesn't like newlines in expressions
    expr = expr.replace("\n","")
    options.append(expr)

    iterations = args.get("iterations")
    other_iterations = args.get("other_iterations")
    if iterations == "other":
        iterations = other_iterations

    iterations = int(iterations)
    if not args.get("exact"):
        options.append(str(iterations))

    return options

def show_results(request):
    if request.method == 'POST':  #this block is only entered when the form is submitted
        try:
            options = parse_options(request.form)
        except Exception as e:
            print("OOPS", e)
            return "Got an error: " + traceback.format_exc()

        p = subprocess.run(
            [str(monaco_bin)] + options,
            capture_output=True,
            text=True
        )
        return f'''<h1>Command: {options}</h1>
        Return code: {p.returncode}<br>
        <pre>
        {p.stdout}
        </pre>
        '''

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    app.run(threaded=True, port=port)

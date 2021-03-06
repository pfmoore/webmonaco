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

@app.route("/test", methods=['POST'])
def test():
    if not request.json:
        return "Error: Invalid JSON"
    with tempfile.TemporaryDirectory() as d:
        cmdfile = Path(d) / "monaco.data"
        with cmdfile.open("w") as f:
            # Suppress "press enter" pause...
            print("-noprompt", file=f)
            for opt in request.json.get("options", []):
                print(opt, file=f)
            expr = request.json["expr"]
            if expr.startswith(("+", "-")):
                expr = "$" + expr
            print(expr, file=f)
            n = request.json.get("count", 10000)
            print("$", n, sep="", file=f)
        command = [str(monaco_bin), str(cmdfile)]
        proc = subprocess.run(command, stdout=subprocess.PIPE, encoding="utf-8")
        return jsonify(dict(stdout=proc.stdout))

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

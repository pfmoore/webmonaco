import os
import stat
import subprocess
import sys
import tempfile
from importlib.resources import read_text
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

monaco_bin = (Path(__file__).parent / f"bin/{sys.platform}/monaco").absolute()
if sys.platform == "linux":
    st = os.stat(monaco_bin)
    os.chmod(monaco_bin, st.st_mode | stat.S_IEXEC)


app = Flask(__name__)
CORS(app)


@app.route("/")
def index():
    with app.open_resource("index.html") as f:
        return f.read()


@app.route("/experimental")
def experimental():
    with app.open_resource("new-index.html") as f:
        return f.read()

@app.route("/run", methods=["GET", "POST"])
def run():
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
        if "expr" in data or "number" in data:
            commands.append("-!")
        if "expr" in data:
            commands.append("$" + data["expr"])
        if "number" in data:
            commands.append("$" + data["number"])
        file_content = "\n".join(commands)

    with tempfile.TemporaryDirectory() as d:
        cmdfile = Path(d) / "monaco.data"
        with cmdfile.open("w") as f:
            # Suppress "press enter" pause, and disallow writing files
            print("-nofiles -noread -noprompt -stderr", file=f)
            print(file_content, file=f)
        command = [str(monaco_bin), cmdfile.name]
        proc = subprocess.run(
            command, capture_output=True, input="", encoding="utf-8", cwd=d
        )

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "command": cmdfile.read_text(),
        }


#if __name__ == "__main__":
#    port = int(os.getenv("PORT", "8080"))
#    app.run(threaded=True, port=port)

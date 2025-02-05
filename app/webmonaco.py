import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path

from flask import Flask, request
from flask_cors import CORS

monaco_bin = (Path(__file__).parent / f"bin/{sys.platform}/monaco").absolute()

app = Flask(__name__)
CORS(app)

@dataclass
class StreamResult:
    truncated: bool
    content: str

@dataclass
class ProcessResult:
    status: str
    rc: int
    out: StreamResult
    err: StreamResult

@app.route("/")
def index():
    with app.open_resource("index.html") as f:
        return f.read()


@app.route("/favicon.ico")
def favicon():
    with app.open_resource("img/favicon.ico") as f:
        return f.read()


@app.route("/help")
def help():
    with app.open_resource("help.html") as f:
        return f.read()

def read_stream(fd, limit) -> StreamResult:
    # Try to read an extra byte to detect truncation If the process outputs
    # *exactly* `limit` characters, and then waits indefinitely before
    # outputting more, the timeout of the process will make this look like we
    # didn't truncate. This isn't expected to be a problem in practice.
    content = fd.read(limit+1)
    truncated = len(content) > limit
    return StreamResult(truncated, content)

def terminate_after(proc, seconds):
    try:
        proc.wait(seconds)
        return "Completed", proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        return "Timeout", -1

# Limits
TIMEOUT = 60     # Maximum runtime (60 seconds)
LIMIT = 100_000  # Maximum output size (100K characters)

def run_and_capture_output(cmd, cwd):
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        text=True,
        cwd=cwd
    )

    with ThreadPoolExecutor() as exc:
        proc_result = exc.submit(terminate_after, proc, TIMEOUT)
        out, err = exc.map(read_stream, (proc.stdout, proc.stderr), (LIMIT, LIMIT))
        status, rc = proc_result.result()

    return ProcessResult(status, rc, out, err)


# Result format example:
# {
#     'status': 'Completed',
#     'rc': 0,
#     'out': {'truncated': False, 'content': 'abc'},
#     'err': {'truncated': False, 'content': 'def'}
# }

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
            print("-nofiles -noread -noprompt +stderr", file=f)
            print(file_content, file=f)
        command = [str(monaco_bin), cmdfile.name]
        result = asdict(run_and_capture_output(command, d))
        result["command"] = command

        return result

# if __name__ == "__main__":
#     port = int(os.getenv("PORT", "8080"))
#     app.run(threaded=True, port=port)

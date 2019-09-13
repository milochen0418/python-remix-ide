from .pylint_errors import pylint_dict_final
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
import eventlet.wsgi
import tempfile, mmap, os, re
from datetime import datetime
from pylint import epylint as lint
from subprocess import Popen, PIPE, STDOUT
from multiprocessing import Pool, cpu_count


is_linux = True
if os.name == "nt":
    is_linux = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['DEBUG'] = True
socketio = SocketIO(app)

num_cores = cpu_count()

@app.route('/')
def index():
    session["count"] = 0
    session["time_now"] = datetime.now()
    return render_template("index.html")


@app.route('/check_code', methods=['POST'])
def check_code():
    session["code"] = request.form['text']
    text = session["code"]
    output = evaluate_pylint(text)
    return jsonify(output)

# Run python in secure system


@app.route('/run_code', methods=['POST'])
def run_code():
    if slow():
        return jsonify("Running code too much. Please wait a few seconds before clicking \"Run\" each time.")
    session["time_now"] = datetime.now()

    output = None
    cmd = 'python ' + session["file_name"]
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE,
              stderr=STDOUT, close_fds=True)
    output = p.stdout.read()

    return jsonify(output.decode('utf-8'))

def slow():
    session["count"] += 1
    time = datetime.now() - session["time_now"]
    if float(session["count"]) / float(time.total_seconds()) > 5:
        return True
    return False

def evaluate_pylint(text):
    try:
        session["file_name"]
        f = open(session["file_name"], "w")
        for t in text:
            f.write(t)
        f.flush()
    except Exception as e:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            session["file_name"] = temp.name
            for t in text:
                temp.write(t.encode("utf-8"))
            temp.flush()
    try:
        ARGS = " -r n --disable=R,C"
        (pylint_stdout, pylint_stderr) = lint.py_run(
            session["file_name"] + ARGS, return_std=True)
    except Exception as e:
        raise Exception(e)

    if pylint_stderr.getvalue():
        raise Exception("Issue with pylint configuration")

    return format_errors(pylint_stdout.getvalue())

def process_error(error):
    if error == " " or error is None:
        return None
    if error.find("Your code has been rated at") > -1:
        return None

    list_words = error.split()
    if len(list_words) < 3:
        return None

    # Detect OS
    line_num = None
    if is_linux:
        try:
            line_num = error.split(":")[1]
        except Exception as e:
            print(os.name + " not compatible: " + e)
    else:
        line_num = error.split(":")[2]

    # list_words.pop(0)
    error_yet, message_yet, first_time = False, False, True
    i, length = 0, len(list_words)
    # error_code=None
    while i < length:
        word = list_words[i]
        if (word == "error" or word == "warning") and first_time:
            error_yet = True
            first_time = False
            i += 1
            continue
        if error_yet:
            error_code = word[1:-1]
            error_string = list_words[i + 1][:-1]
            i = i + 3
            error_yet = False
            message_yet = True
            continue
        if message_yet:
            full_message = ' '.join(list_words[i:length - 1])
            break
        i += 1

    error_info = pylint_dict_final[error_code]

    return {
        "code": error_code,
        "error": error_string,
        "message": full_message,
        "line": line_num,
        "error_info": error_info,
    }

def format_errors(pylint_text):
    errors_list = pylint_text.splitlines(True)
    if "--------------------------------------------------------------------" in errors_list[1] and "Your code has been rated at" in errors_list[2] and "module" not in errors_list[0]:
        return None

    errors_list.pop(0)

    pylint_dict = {}
    try:
        pool = Pool(num_cores)
        pylint_dict = pool.map(process_error, errors_list)
    finally:
        pool.close()
        pool.join()
        return pylint_dict
    return pylint_dict

@socketio.on('disconnect', namespace='/check_disconnect')
def disconnect():
    os.remove(session["file_name"])
if __name__ == "__main__":
    socketio.run(app)

from flask import Flask, render_template, jsonify, Response, request, redirect, session
import backend.metrics.SystemMetrics as sm
import backend.metrics.MethodScheduler as ms
import backend.charts.BokehCharts as bc
import backend.database.Database as Database
import datetime
import threading
import time
import json
import sched
import bcrypt

app = Flask(__name__)
app.secret_key = 'secret_key'

system_metrics = sm.SystemMetrics()
method_scheduler = ms.MethodScheduler
bokeh_chart = bc.BokehCharts()
json_update_event = threading.Event()

# Function to collect and print metrics
def collect_metrics():
    print(f"Collecting system metrics... {time.strftime('%H:%M:%S', time.localtime())}")
    db = Database.Database("sma_prod.db")
    cursor = db.getCursor()
    metrics = system_metrics.get_all_info()
    disk_average = sum([disk["percent"] for disk in metrics['disk']]) / len(metrics['disk'])
    db.addSystemMetrics(metrics['cpu']['usage'], metrics['memory']['percent'], disk_average)

    for index, process in enumerate(metrics['process']):
        db.addProcessMetrics(process['pid'], process['name'], process['cpu_times'].system or 0,
                        process['cpu_percent'], process['memory_percent'])

def prune_metrics():
    db = Database.Database("sma_prod.db")
    db.pruneData()


def update_live_view():
    print(f"Updating live view... {time.strftime('%H:%M:%S', time.localtime())}")
    json_update_event.set()

@app.before_request
def before_request():
    if not session.get('logged_in'):
        session['logged_in'] = False
    if not session.get('role'):
        session['role'] = ""

@app.route('/')
def home():
    figure_dict = bokeh_chart.get_charts()
    # This route renders the HTML template for the dashboard.
    return render_template('index.html', cpu_usage=figure_dict['cpu_usage'], mem_usage=figure_dict['mem_usage'],
                            logged_in=session['logged_in'], role=session['role'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username', "")

    if request.form:
        password = request.form['password']
        db = Database.Database("sma_prod.db")

        if db.isValidLogon(username, password):
            session['logged_in'] = True
            session['role'] = db.getUserRole(username)[0][0]
            return redirect('/')

    return render_template('login.html', username=username)

@app.route('/logout', methods=['GET'])
def logout():
    session['logged_in'] = False
    return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    username = request.form.get('username', "")

    if request.form:
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        db = Database.Database("sma_prod.db")

        db.addUser(username, hashed_password, 'User')
        return redirect('/login')

    return render_template('register.html', username=username)

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if request.form:
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        if datetime.datetime.strptime(end_date, "%Y-%m-%d") < datetime.datetime.strptime(start_date, "%Y-%m-%d"):
            return render_template('report.html', systemMetrics="undefined", processMetrics="undefined",
                                    processes="undefined", error="Start Date should be before End Date.")

        db = Database.Database("sma_prod.db")
        system_metrics = db.get_system_metrics_date_range(request.form['start_date'], request.form['end_date'])
        process_metrics = db.get_process_metrics_date_range(request.form['start_date'], request.form['end_date'])
        processes_ids = set()
        processes_ids |= { int(x[0]) for x in process_metrics }
        processes_ids = list(processes_ids)
        processes = {process[0]: process[1] for process in db.get_process_by_id(processes_ids)}
        return render_template('report.html', systemMetrics=system_metrics, processMetrics=process_metrics,
                                processes=processes, success="Report download will begin in just a moment...",
                                logged_in=session['logged_in'], role=session['role'])

    # This route renders the HTML template for the report view.
    return render_template('report.html', systemMetrics="undefined", processMetrics="undefined", processes="undefined",
                                logged_in=session['logged_in'], role=session['role'])

@app.route('/api/metrics/realtime', methods=['GET'])
def all_api_metrics():
    def generate():
        while True:
            if json_update_event.wait(timeout=None):
                yield 'data: {}\n\n'.format(json.dumps(system_metrics.get_all_info()))
                json_update_event.clear()

    return Response(generate(), mimetype="text/event-stream")

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if 'id' in json.loads(request.data) and json.loads(request.data)['id'] == 'deleteUser':
            username = json.loads(request.data)['username']
            db = Database.Database("sma_prod.db")
            db.deleteUser(username)

        if 'username' in json.loads(request.data) and 'newRole' in json.loads(request.data):
            username = json.loads(request.data)['username']
            newRole = json.loads(request.data)['newRole']
            db = Database.Database("sma_prod.db")
            db.updateUserRole(username, newRole)

        return jsonify({'status': 200})

    if session.get('logged_in') and session.get('role') == 'Admin':
        db = Database.Database("sma_prod.db")
        users = db.getUsers()
        return render_template('admin.html', logged_in=session['logged_in'], users=[{'username': u, 'role': r} for u, r in users],
                            role=session['role'])

    return redirect('/')

if __name__ == '__main__':
    metric_scheduler = method_scheduler(collect_metrics, interval=30)
    live_view_scheduler = method_scheduler(update_live_view, interval=1)
    prune_metrics_scheduler = method_scheduler(prune_metrics, interval=43200) # 12 hours

    # Start the Flask app
    app.run(threaded=True, use_reloader=False)  # use_reloader=False if you don't want the app to restart twice

from flask import Flask, render_template, jsonify, Response, request, redirect
import backend.metrics.SystemMetrics as sm
import backend.metrics.MethodScheduler as ms
import backend.charts.BokehCharts as bc
import backend.database.Database as Database
import threading
import time
import json
import sched
import bcrypt

app = Flask(__name__)

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
        db.addProcessMetrics(process['pid'], process['name'], process['cpu_times'][1],
                        process['cpu_percent'], process['memory_percent'])

def update_live_view():
    print(f"Updating live view... {time.strftime('%H:%M:%S', time.localtime())}")
    json_update_event.set()

# @app.before_request
# def before_request():
#     return render_template('login.html')

@app.route('/')
def home():
    figure_dict = bokeh_chart.get_charts()
    # This route renders the HTML template for the dashboard.
    return render_template('index.html', cpu_usage=figure_dict['cpu_usage'], mem_usage=figure_dict['mem_usage'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username', "")

    if request.form:
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        if bcrypt.checkpw('world'.encode(), hashed_password):
            return redirect('/')

    return render_template('login.html', username=username)

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    if request.form:
        db = Database.Database("sma_prod.db")
        system_metrics = db.get_system_metrics_date_range(request.form['start_date'], request.form['end_date'])
        process_metrics = db.get_process_metrics_date_range(request.form['start_date'], request.form['end_date'])
        processes_ids = set()
        processes_ids |= { int(x[0]) for x in process_metrics }
        processes_ids = list(processes_ids)
        processes = db.get_process_by_id(processes_ids)
        return render_template('report.html', systemMetrics=system_metrics, processMetrics=process_metrics, processes=processes)

    # This route renders the HTML template for the report view.
    return render_template('report.html', systemMetrics="", processMetrics="", processes="")

@app.route('/api/metrics/realtime', methods=['GET'])
def all_api_metrics():
    def generate():
        while True:
            if json_update_event.wait(timeout=None):
                json_update_event.clear()
                yield 'data: {}\n\n'.format(json.dumps(system_metrics.get_all_info()))

    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    metric_scheduler = method_scheduler(collect_metrics, interval=30)
    live_view_scheduler = method_scheduler(update_live_view, interval=1)

    # Start the Flask app
    app.run(use_reloader=False)  # use_reloader=False if you don't want the app to restart twice

from flask import Flask, render_template, jsonify, Response, request, redirect
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
import logging
from logging.handlers import RotatingFileHandler
import os 

app = Flask(__name__)

system_metrics = sm.SystemMetrics()
method_scheduler = ms.MethodScheduler
bokeh_chart = bc.BokehCharts()
json_update_event = threading.Event()

def setup_logging():
    log_format = ("%(asctime)s %(threadName)s %(levelname)s %(module)s.%(funcName)s():%(lineno)s %(message)s")
    log_folder = "log"
    log_filename = "system-metrics-analyzer.log"
    log_num_backups = 10
    log_max_file_bytes = 100000 #100kb
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    if not os.path.isdir(log_folder):
        os.mkdir(log_folder)
    log_filepath = os.path.join(log_folder, log_filename)
    rotating_log_file_handler = RotatingFileHandler(log_filepath, maxBytes=log_max_file_bytes, backupCount=log_num_backups)
    rotating_log_file_handler.setLevel(logging.DEBUG)
    rotating_log_file_handler.setFormatter(logging.Formatter(log_format))
    root_logger = logging.getLogger("")
    root_logger.addHandler(rotating_log_file_handler)

# Function to collect and print metrics
def collect_metrics():
    logging.debug("->")
    print(f"Collecting system metrics... {time.strftime('%H:%M:%S', time.localtime())}")
    db = Database.Database("sma_prod.db")
    cursor = db.getCursor()
    metrics = system_metrics.get_all_info()
    disk_average = sum([disk["percent"] for disk in metrics['disk']]) / len(metrics['disk'])
    db.addSystemMetrics(metrics['cpu']['usage'], metrics['memory']['percent'], disk_average)

    for index, process in enumerate(metrics['process']):
        db.addProcessMetrics(process['pid'], process['name'], process['cpu_times'][1],
                        process['cpu_percent'], process['memory_percent'])
    logging.debug("<-")

def update_live_view():
    print(f"Updating live view... {time.strftime('%H:%M:%S', time.localtime())}")
    json_update_event.set()

# @app.before_request
# def before_request():
#     return render_template('login.html')

@app.route('/')
def home():
    logging.debug("->")
    figure_dict = bokeh_chart.get_charts()
    # This route renders the HTML template for the dashboard.
    return render_template('index.html', cpu_usage=figure_dict['cpu_usage'], mem_usage=figure_dict['mem_usage'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    logging.debug("->")
    username = request.form.get('username', "")

    if request.form:
        password = request.form['password']
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        if bcrypt.checkpw('world'.encode(), hashed_password):
            return redirect('/')

    return render_template('login.html', username=username)

@app.route('/reports', methods=['GET', 'POST'])
def reports():
    logging.debug("->")
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
                                processes=processes, success="Report download will begin in just a moment...")

    # This route renders the HTML template for the report view.
    return render_template('report.html', systemMetrics="undefined", processMetrics="undefined", processes="undefined")

@app.route('/api/metrics/realtime', methods=['GET'])
def all_api_metrics():
    logging.debug("->")
    def generate():
        while True:
            if json_update_event.wait(timeout=None):
                yield 'data: {}\n\n'.format(json.dumps(system_metrics.get_all_info()))
                json_update_event.clear()

    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    setup_logging()
    logging.info("*****STARTING SMA*****")
    metric_scheduler = method_scheduler(collect_metrics, interval=30)
    live_view_scheduler = method_scheduler(update_live_view, interval=1)

    # Start the Flask app
    app.run(threaded=True, use_reloader=False)  # use_reloader=False if you don't want the app to restart twice
    logging.info("Flask app is running")

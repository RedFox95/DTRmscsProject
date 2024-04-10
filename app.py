from flask import Flask, render_template, jsonify, Response, request, redirect
import backend.metrics.SystemMetrics as sm
import backend.charts.BokehCharts as bc
import threading
import time
import json
import sched
import bcrypt

app = Flask(__name__)

system_metrics = sm.SystemMetrics()
bokeh_chart = bc.BokehCharts()
wait_interval = 1

# Function to collect and print metrics
def collect_metrics():
    print("Collecting system metrics...")

# Function to be scheduled
def scheduled_task(sc):
    collect_metrics()  # Call the metric collection function
    sc.enter(wait_interval, 1, scheduled_task, (sc,))  # Schedule the next call

# Start the scheduler in a separate thread
def start_scheduler():
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(wait_interval, 1, scheduled_task, (scheduler,))
    scheduler.run()

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

@app.route('/reports', methods=['GET'])
def reports():
    # This route renders the HTML template for the report view.
    return render_template('report.html')

@app.route('/cpu-stream', methods=['GET'])
def cpu_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(system_metrics.get_cpu_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/memory-stream', methods=['GET'])
def mem_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(system_metrics.get_memory_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/disk-stream', methods=['GET'])
def disk_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(system_metrics.get_disk_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/process-stream', methods=['GET'])
def process_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(system_metrics.get_process_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

if __name__ == '__main__':
    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=start_scheduler)
    #scheduler_thread.start()

    # Start the Flask app
    app.run(use_reloader=False)  # use_reloader=False if you don't want the app to restart twice

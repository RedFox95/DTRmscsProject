from flask import Flask, render_template, jsonify, Response, request, redirect
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.io import curdoc
from bokeh.models import ColumnDataSource, CustomJS
from bokeh.themes import Theme
from random import randint
import metrics.SystemMetrics as sm
import threading
import time
import json
import sched

app = Flask(__name__)

system_metrics = sm.SystemMetrics()
wait_interval = 2

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

def get_cpu_chart():
    x = [i for i in range(61)][::-1]
    y = list(system_metrics.cpu_chart_buffer)

    p = figure(name='cpu_usage', x_axis_label='Seconds', y_axis_label='%', tools='', x_range=(60, 0),
                height=900, width=1600, sizing_mode='stretch_both', y_axis_location='right')
    p.line(x, y, legend_label="cpu usage", line_width=2, line_color='#b31b1b')
    p.legend.location = 'top_left'
    p.legend.background_fill_color = "#232323"
    p.legend.label_text_color = "#a8a8a8"
    p.toolbar.logo = None
    curdoc().theme = Theme(filename='./theme/theme.json')
    curdoc().add_root(p)

    return components(p)

def get_mem_chart():
    x = [i for i in range(61)][::-1]
    y = list(system_metrics.mem_chart_buffer)

    p = figure(name='mem_usage', x_axis_label='Seconds', y_axis_label='%', tools='', x_range=(60, 0),
                y_range=(0, 100), height=900, width=1600, sizing_mode='stretch_both', y_axis_location='right')
    p.line(x, y, legend_label="memory usage", line_width=2, line_color='#b31b1b')
    p.legend.location = 'top_left'
    p.legend.background_fill_color = "#232323"
    p.legend.label_text_color = "#a8a8a8"
    p.toolbar.logo = None
    curdoc().theme = Theme(filename='./theme/theme.json')
    curdoc().add_root(p)

    return components(p)

# @app.before_request
# def before_request():
#     return render_template('login.html')

@app.route('/')
def home():
    print(system_metrics.get_cpu_info())
    cpu_script, cpu_div = get_cpu_chart()
    mem_script, mem_div = get_mem_chart()

    # This route renders the HTML template for the dashboard.
    return render_template('index.html', cpu_script=cpu_script, cpu_div=cpu_div, mem_script=mem_script, mem_div=mem_div)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.form:
        username = request.form['username']
        password = request.form['password']

        if username == "test1" and password == "test2":
            return redirect('/')

    # This route renders the HTML template for the dashboard.
    return render_template('login.html')

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

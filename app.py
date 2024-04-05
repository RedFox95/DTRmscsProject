from flask import Flask, render_template, jsonify, Response, request, redirect
from datetime import timedelta
import psutil
import threading
import time
import json
import sched

app = Flask(__name__)

wait_interval = 30

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

def get_cpu_info():
    freq = psutil.cpu_freq()
    boot_time = psutil.boot_time()
    current_time = time.time()
    uptime_seconds = current_time - boot_time
    uptime = format_cpu_time(uptime_seconds)

    cpu_data = {
        'speed': freq.current,  # Round to 2 decimal places for GB
        'uptime': uptime,
        'logical': psutil.cpu_count(),
        'physical': psutil.cpu_count(logical=False)
    }

    return cpu_data

def get_memory_info():
    memory = psutil.virtual_memory()
    total_memory_gb = memory.total / (1024 ** 3)  # Convert bytes to GB
    used_memory_gb = memory.used / (1024 ** 3)  # Convert bytes to GB
    memory_percent = memory.percent  # Percentage of memory used

    return {
        'total': round(total_memory_gb, 2),  # Round to 2 decimal places for GB
        'used': round(used_memory_gb, 2),
        'percent': memory_percent
    }

def get_disk_info():
    disks = []
    for partition in psutil.disk_partitions():
        usage = psutil.disk_usage(partition.mountpoint)
        disks.append({
            'device': partition.device,
            'mountpoint': partition.mountpoint,
            'total': round(usage.total / (1024 ** 3), 2),  # Convert to GB
            'used': round(usage.used / (1024 ** 3), 2),  # Convert to GB
            'percent': usage.percent
        })
    return disks

def get_process_info():
    processes = []
    for process in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'cpu_times', 'create_time']):
        try:
            processes.append(process.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes[0:10]

# @app.before_request
# def before_request():
#     return render_template('login.html')

@app.route('/')
def home():
    # This route renders the HTML template for the dashboard.
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.form:
        username = request.form['username']
        password = request.form['password']

        if username == "test1" and password == "test2":
            return redirect('/')

    # This route renders the HTML template for the dashboard.
    return render_template('login.html')

@app.route('/reports')
def reports():
    # This route renders the HTML template for the report view.
    return render_template('report.html')

@app.route('/cpu-stream')
def cpu_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(get_cpu_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/memory-stream')
def mem_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(get_memory_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/disk-stream')
def disk_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(get_disk_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/process-stream')
def process_stream():
    def generate():
        while True:
            yield 'data: {}\n\n'.format(json.dumps(get_process_info()))
            time.sleep(wait_interval)

    return Response(generate(), mimetype="text/event-stream")

@app.route('/cpu_usage')
def cpu_usage():
    cpu_usage_data = {
        'percent': psutil.cpu_percent(interval=1),
        'physical_count': get_physical_core_count(),
        'logical_count': get_logical_core_count(),
        'speed': get_cpu_speed(),
        'uptime': get_cpu_uptime()
    }
    return jsonify(cpu_usage_data)

@app.route('/api/system_metrics')
def api_system_metrics():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = get_memory_info()
    disk_info = get_disk_info()
    process_info = get_process_info()

    response_data = {
        'cpu_usage': {
            'percent': cpu_percent,
            'physical_count': get_physical_core_count(),
            'logical_count': get_logical_core_count(),
            'speed': get_cpu_speed(),
            'uptime': get_cpu_uptime()
        },
        'memory_info': memory_info,
        'disk_info': disk_info,
        'process_info': process_info
    }
    return jsonify(response_data)

def format_cpu_time(t):
    td = timedelta(seconds=t)
    days, remainder = divmod(td.total_seconds(), 86400) # 86400 seconds in a day
    hours, remainder = divmod(remainder, 3600) # 3600 minutes in a day
    minutes, seconds = divmod(remainder, 60)

    cpu_time = ""
    if days > 0:
        cpu_time += f"{round(days)} day(s), "
    if hours > 0:
        cpu_time += f"{round(hours)} hour(s), "
    if minutes > 0:
        cpu_time += f"{round(minutes)} minute(s), "
    if seconds > 0:
        cpu_time += f"{round(seconds)} second(s)"

    return cpu_time

if __name__ == '__main__':
    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()

    # Start the Flask app
    app.run(use_reloader=False)  # use_reloader=False if you don't want the app to restart twice

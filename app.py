import sched
import time
import psutil
import threading
from datetime import timedelta
from flask import Flask, render_template, jsonify

app = Flask(__name__)

# Function to collect and print metrics
def collect_metrics():
    print("Collecting system metrics...")
    # Your existing metrics collection logic

# Function to be scheduled
def scheduled_task(sc):
    collect_metrics()  # Call the metric collection function
    sc.enter(30, 1, scheduled_task, (sc,))  # Schedule the next call

# Start the scheduler in a separate thread
def start_scheduler():
    scheduler = sched.scheduler(time.time, time.sleep)
    scheduler.enter(30, 1, scheduled_task, (scheduler,))
    scheduler.run()

def get_cpu_info():
    freq = psutil.cpu_freq()
    boot_time = psutil.boot_time()
    current_time = time.time()
    uptime_seconds = current_time - boot_time
    # Format the uptime into a more readable format, e.g., "2 days, 4:52:15"
    uptime = str(timedelta(seconds=uptime_seconds))

    return {
        'speed': freq.current,  # Round to 2 decimal places for GB
        'uptime': uptime,
        'logical': psutil.cpu_count(),
        'physical': psutil.cpu_count(logical=False)
    }

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
            'total': usage.total / (1024 ** 3),  # Convert to GB
            'used': usage.used / (1024 ** 3),  # Convert to GB
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
    return processes



@app.route('/')
def home():
    # This route renders the HTML template for the dashboard.
    return render_template('index.html',
                            cpu=get_cpu_info(),
                            memory=get_memory_info(),
                            )


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





if __name__ == '__main__':
    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()

    # Start the Flask app
    app.run(use_reloader=False)  # use_reloader=False if you don't want the app to restart twice

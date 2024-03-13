import sched
import time
import psutil
import threading
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

@app.route('/')
def system_metrics():
    # Example of using psutil within a route
    cpu_percent = psutil.cpu_percent(interval=1)
    return render_template('index.html', cpu_percent=cpu_percent)

@app.route('/cpu_usage')
def cpu_usage():
    cpu_percent = psutil.cpu_percent(interval=1)
    return jsonify(cpu_percent=cpu_percent)


if __name__ == '__main__':
    # Start the scheduler thread
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.start()

    # Start the Flask app
    app.run(use_reloader=False)  # use_reloader=False if you don't want the app to restart twice

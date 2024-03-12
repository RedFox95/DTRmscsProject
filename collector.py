import psutil
import sched
import time
from models import db, CPU, Memory, Disk, Process
from app import app

# Create a scheduler instance
scheduler = sched.scheduler(time.time, time.sleep)

def collect_and_store(sc):
    with app.app_context():
        # Collect CPU info
        physical_count = psutil.cpu_count(logical=False)
        logical_count = psutil.cpu_count()
        speed = psutil.cpu_freq().current if psutil.cpu_freq() else 0  # Ensure cpu_freq is not None

        # Create a new CPU instance with the collected data
        cpu = CPU(
            physical_count=physical_count,
            logical_count=logical_count,
            speed=speed
        )

        # Add the new CPU instance to the session and commit it to the database
        db.session.add(cpu)
        db.session.commit()

        # Schedule the next call to collect_and_store
        sc.enter(30, 1, collect_and_store, (sc,))

if __name__ == '__main__':
    # Schedule the first call to collect_and_store
    scheduler.enter(0, 1, collect_and_store, (scheduler,))
    scheduler.run()

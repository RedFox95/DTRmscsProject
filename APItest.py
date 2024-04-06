import requests
import unittest
import datetime
import sqlite3

class APITestCase(unittest.TestCase):
    BASE_URL = "http://localhost:5000/api"

    def setUp(self):
        """Setup method to prepare any prerequisites for the tests."""
        # Connect to the test database
        self.conn = sqlite3.connect('path/to/test_database.db')
        self.cursor = self.conn.cursor()

        # Insert test data for system metrics
        self.cursor.execute('''INSERT INTO SystemMetrics (cpu, memory, disk, cpu_physical_count, cpu_logical_count, cpu_speed, timestamp) 
                               VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                               ('25%', '40%', '30%', 8, 8, 3.2, datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')))

        # Insert test data for realtime metrics
        self.cursor.execute('''INSERT INTO RealtimeMetrics (metric_type, value, timestamp) 
                               VALUES (?, ?, ?)''', 
                               ('cpu', '25%', datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')))
        
        # Save (commit) the changes
        self.conn.commit()

    def tearDown(self):
        """Cleanup method to remove any data after tests are done."""
        # Delete test data to ensure a clean database state
        self.cursor.execute('DELETE FROM SystemMetrics WHERE cpu_physical_count=?', (8,))
        self.cursor.execute('DELETE FROM RealtimeMetrics WHERE metric_type=?', ('cpu',))
        
        # Save (commit) the changes and close the connection
        self.conn.commit()
        self.conn.close()
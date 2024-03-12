from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class CPU(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    physical_count = db.Column(db.Integer)
    logical_count = db.Column(db.Integer)
    speed = db.Column(db.Float)

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer)
    available = db.Column(db.Integer)

class Disk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer)
    available = db.Column(db.Integer)

class Process(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    pid = db.Column(db.Integer)
    execution_time = db.Column(db.Float)
    cpu_utilization = db.Column(db.Float)
    memory_utilization = db.Column(db.Float)

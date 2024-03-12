from flask import Flask, render_template
from models import db, CPU, Memory, Disk, Process

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///system_info.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/')
def index():
    # Example: Fetch all CPU records
    cpus = CPU.query.all()
    print(cpus)  # Debugging: Print fetched data
    return render_template('index.html', cpus=cpus)

def setup_database():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
    setup_database()
    app.run(debug=True)

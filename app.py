from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/healthbot')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# Create uploads directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============ DATABASE MODELS ============

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reports = db.relationship('HealthReport', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }


class HealthReport(db.Model):
    __tablename__ = 'health_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    report_data = db.Column(db.JSON, nullable=True)
    health_score = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(50), nullable=True)  # Low, Moderate, High
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat(),
            'report_data': self.report_data,
            'health_score': self.health_score,
            'risk_level': self.risk_level
        }


class TestValue(db.Model):
    __tablename__ = 'test_values'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('health_reports.id'), nullable=False)
    test_name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    reference_range = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=True)  # Normal, Low, High
    
    def to_dict(self):
        return {
            'id': self.id,
            'test_name': self.test_name,
            'value': self.value,
            'unit': self.unit,
            'reference_range': self.reference_range,
            'status': self.status
        }

# ============ ROUTES ============

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'HealthBot API is running'}), 200


@app.route('/api/users', methods=['POST'])
def create_user():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('name'):
            return jsonify({'error': 'Email and name are required'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        user = User(email=data['email'], name=data['name'])
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'User created', 'user': user.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports', methods=['POST'])
def upload_report():
    try:
        if 'file' not in request.files or 'user_id' not in request.form:
            return jsonify({'error': 'File and user_id are required'}), 400
        
        file = request.files['file']
        user_id = request.form['user_id']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        report = HealthReport(
            user_id=user_id,
            filename=filename,
            file_path=filepath
        )
        db.session.add(report)
        db.session.commit()
        
        return jsonify({'message': 'Report uploaded', 'report': report.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from utils.report_processor import ReportProcessor
from utils.health_analyzer import HealthAnalyzer
from utils.hospital_recommender import HospitalRecommender
from datetime import datetime

load_dotenv()

app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/healthbot')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

report_processor = ReportProcessor()
health_analyzer = HealthAnalyzer()
hospital_recommender = HospitalRecommender()

# ============ SERVE REACT FRONTEND ============

@app.route('/')
def serve_react():
    """Serve React frontend"""
    try:
        return send_from_directory('frontend/build', 'index.html')
    except:
        return jsonify({'error': 'Frontend not built'}), 404

@app.route('/<path:path>')
def static_files(path):
    """Serve static files"""
    try:
        if path and '.' in path:
            return send_from_directory('frontend/build', path)
        return send_from_directory('frontend/build', 'index.html')
    except:
        return send_from_directory('frontend/build', 'index.html')

# ============ DATABASE MODELS ============

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    location_lat = db.Column(db.Float, nullable=True)
    location_long = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    reports = db.relationship('HealthReport', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'age': self.age,
            'gender': self.gender,
            'created_at': self.created_at.isoformat()
        }


class HealthReport(db.Model):
    __tablename__ = 'health_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_text = db.Column(db.Text, nullable=True)
    health_score = db.Column(db.Float, nullable=True)
    risk_level = db.Column(db.String(50), nullable=True)
    analysis_data = db.Column(db.JSON, nullable=True)
    
    test_values = db.relationship('TestValue', backref='report', lazy=True, cascade='all, delete-orphan')
    hospital_recommendations = db.relationship('HospitalRecommendation', backref='report', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'filename': self.filename,
            'uploaded_at': self.uploaded_at.isoformat(),
            'health_score': self.health_score,
            'risk_level': self.risk_level,
            'analysis_data': self.analysis_data
        }


class TestValue(db.Model):
    __tablename__ = 'test_values'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('health_reports.id'), nullable=False)
    test_name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    reference_range = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'test_name': self.test_name,
            'value': self.value,
            'unit': self.unit,
            'reference_range': self.reference_range,
            'status': self.status,
            'category': self.category
        }


class HospitalRecommendation(db.Model):
    __tablename__ = 'hospital_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, db.ForeignKey('health_reports.id'), nullable=False)
    hospital_name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    specialties = db.Column(db.JSON, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    recommendation_reason = db.Column(db.Text, nullable=True)
    score = db.Column(db.Float, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'hospital_name': self.hospital_name,
            'city': self.city,
            'specialties': self.specialties,
            'rating': self.rating,
            'recommendation_reason': self.recommendation_reason,
            'score': self.score
        }

# ============ API ROUTES ============

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
        
        user = User(
            email=data['email'],
            name=data['name'],
            age=data.get('age'),
            gender=data.get('gender'),
            location_lat=data.get('location_lat'),
            location_long=data.get('location_long')
        )
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


@app.route('/api/reports/<report_id>/analyze', methods=['POST'])
def analyze_report(report_id):
    try:
        report = HealthReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        processing_result = report_processor.process_report(report.file_path)
        
        if 'error' in processing_result:
            return jsonify({'error': processing_result['error']}), 400
        
        test_values = processing_result['test_values']
        
        analysis = health_analyzer.analyze_health_data(test_values)
        
        user_location = None
        if report.user.location_lat and report.user.location_long:
            user_location = (report.user.location_lat, report.user.location_long)
        
        hospital_recs = hospital_recommender.recommend_hospitals(
            analysis.get('abnormalities', []),
            user_location
        )
        
        report.raw_text = processing_result.get('raw_text', '')
        report.health_score = analysis['health_score']
        report.risk_level = analysis['risk_level']
        report.analysis_data = {
            'summary': analysis['summary'],
            'insights': analysis['insights'],
            'recommendations': analysis['recommendations'],
            'red_flags': analysis['red_flags']
        }
        db.session.commit()
        
        for test in test_values:
            test_value = TestValue(
                report_id=report.id,
                test_name=test['test_name'],
                value=test.get('value'),
                unit=test.get('unit'),
                reference_range=test.get('reference_range'),
                status=test['status'],
                category=test.get('category')
            )
            db.session.add(test_value)
        
        for rec in hospital_recs:
            hosp_rec = HospitalRecommendation(
                report_id=report.id,
                hospital_name=rec['name'],
                city=rec['city'],
                specialties=rec['specialties'],
                rating=rec['rating'],
                recommendation_reason=rec['recommended_for'],
                score=rec['score']
            )
            db.session.add(hosp_rec)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Report analyzed successfully',
            'analysis': analysis,
            'hospital_recommendations': hospital_recs,
            'report': report.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error analyzing report: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    try:
        report = HealthReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        test_values = TestValue.query.filter_by(report_id=report_id).all()
        hospital_recs = HospitalRecommendation.query.filter_by(report_id=report_id).all()
        
        return jsonify({
            'report': report.to_dict(),
            'test_values': [tv.to_dict() for tv in test_values],
            'hospital_recommendations': [hr.to_dict() for hr in hospital_recs],
            'analysis_data': report.analysis_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/<user_id>/reports', methods=['GET'])
def get_user_reports(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        reports = HealthReport.query.filter_by(user_id=user_id).all()
        return jsonify({
            'user': user.to_dict(),
            'reports': [r.to_dict() for r in reports],
            'total_reports': len(reports)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/<report_id>/export', methods=['GET'])
def export_report(report_id):
    try:
        report = HealthReport.query.get(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        test_values = TestValue.query.filter_by(report_id=report_id).all()
        hospital_recs = HospitalRecommendation.query.filter_by(report_id=report_id).all()
        
        export_data = {
            'report': report.to_dict(),
            'test_values': [tv.to_dict() for tv in test_values],
            'hospital_recommendations': [hr.to_dict() for hr in hospital_recs],
            'analysis': report.analysis_data,
            'exported_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(export_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
from typing import Dict, List, Tuple
from datetime import datetime

class HealthAnalyzer:
    """Advanced health analysis and scoring system"""
    
    CATEGORY_WEIGHTS = {
        'Blood': 0.25,
        'Lipid': 0.20,
        'Metabolic': 0.20,
        'Kidney': 0.15,
        'Thyroid': 0.10,
        'Vitamin': 0.10
    }

    def analyze_health_data(self, test_values: List[Dict]) -> Dict:
        """Comprehensive health analysis"""
        
        if not test_values:
            return {
                'health_score': 0,
                'risk_level': 'Unknown',
                'summary': 'No test data available',
                'abnormalities': [],
                'insights': []
            }
        
        health_score = self.calculate_health_score(test_values)
        risk_level = self.determine_risk_level(health_score)
        abnormalities = self.identify_abnormalities(test_values)
        insights = self.generate_insights(test_values, abnormalities)
        red_flags = self.identify_red_flags(test_values)
        recommendations = self.generate_recommendations(test_values)
        
        return {
            'health_score': health_score,
            'risk_level': risk_level,
            'summary': self.generate_summary(health_score, risk_level),
            'abnormalities': abnormalities,
            'insights': insights,
            'red_flags': red_flags,
            'recommendations': recommendations,
            'test_breakdown': self.categorize_tests(test_values),
            'analyzed_at': datetime.utcnow().isoformat()
        }

    def calculate_health_score(self, test_values: List[Dict]) -> float:
        """Calculate overall health score (0-100)"""
        if not test_values:
            return 0
        
        base_score = 100
        category_scores = {}
        
        for test in test_values:
            category = test.get('category', 'Other')
            status = test.get('status', 'Normal')
            
            if category not in category_scores:
                category_scores[category] = {'tests': [], 'deductions': 0}
            
            category_scores[category]['tests'].append(test)
            
            if status == 'High':
                category_scores[category]['deductions'] += 5
            elif status == 'Low':
                category_scores[category]['deductions'] += 5
        
        total_weight = 0
        weighted_deduction = 0
        
        for category, data in category_scores.items():
            weight = self.CATEGORY_WEIGHTS.get(category, 0.10)
            deduction = min(data['deductions'], 20)
            weighted_deduction += deduction * weight
            total_weight += weight
        
        health_score = base_score - weighted_deduction
        return max(0, min(100, health_score))

    def determine_risk_level(self, health_score: float) -> str:
        """Determine overall risk level"""
        if health_score >= 75:
            return 'Low'
        elif health_score >= 50:
            return 'Moderate'
        else:
            return 'High'

    def identify_abnormalities(self, test_values: List[Dict]) -> List[Dict]:
        """Identify all abnormal values"""
        abnormalities = []
        
        for test in test_values:
            if test.get('status') != 'Normal':
                abnormalities.append({
                    'test_name': test['test_name'],
                    'value': test['value'],
                    'unit': test['unit'],
                    'status': test['status'],
                    'reference_range': test['reference_range'],
                    'severity': self.calculate_severity(test)
                })
        
        abnormalities.sort(key=lambda x: x['severity'], reverse=True)
        return abnormalities

    def calculate_severity(self, test: Dict) -> int:
        """Calculate severity of abnormality (0-10)"""
        status = test.get('status', 'Normal')
        value = test.get('value', 0)
        
        try:
            reference_range = test.get('reference_range', '0-100').split('-')
            min_val = float(reference_range[0])
            max_val = float(reference_range[1])
            range_width = max_val - min_val
            
            if status == 'Normal':
                return 0
            elif status == 'Low':
                deviation = (min_val - value) / range_width
            else:
                deviation = (value - max_val) / range_width
            
            severity = min(10, int(abs(deviation) * 10))
            return severity
        except:
            return 5 if status != 'Normal' else 0

    def identify_red_flags(self, test_values: List[Dict]) -> List[Dict]:
        """Identify critical values needing urgent attention"""
        red_flags = []
        
        critical_thresholds = {
            'blood_sugar': {'min': 40, 'max': 400},
            'hemoglobin': {'min': 7, 'max': 20},
        }
        
        for test in test_values:
            test_name = test['test_name'].lower().replace(' ', '_')
            value = test.get('value', 0)
            
            if test_name in critical_thresholds:
                thresholds = critical_thresholds[test_name]
                if value < thresholds['min'] or value > thresholds['max']:
                    red_flags.append({
                        'test_name': test['test_name'],
                        'value': value,
                        'unit': test['unit'],
                        'message': f"Critical value detected: {value} {test['unit']}. Seek medical attention.",
                        'urgency': 'HIGH'
                    })
        
        return red_flags

    def generate_insights(self, test_values: List[Dict], abnormalities: List[Dict]) -> List[str]:
        """Generate personalized health insights"""
        insights = []
        
        abnormal_count = len(abnormalities)
        total_count = len(test_values)
        
        if abnormal_count == 0:
            insights.append("✓ All test values are within normal ranges")
        else:
            insights.append(f"⚠️ {abnormal_count} out of {total_count} values are abnormal")
        
        lipid_tests = [a for a in abnormalities if 'cholesterol' in a['test_name'].lower() or 'triglycerides' in a['test_name'].lower()]
        if lipid_tests:
            insights.append("💛 High cholesterol detected: Consider reducing saturated fats and increasing exercise")
        
        sugar_tests = [a for a in abnormalities if 'blood_sugar' in a['test_name'].lower()]
        if sugar_tests:
            insights.append("🍬 Blood sugar abnormality: Monitor carbohydrate intake and consult a nutritionist")
        
        vitamin_tests = [a for a in abnormalities if 'vitamin' in a['test_name'].lower()]
        if vitamin_tests:
            insights.append("💊 Vitamin deficiency detected: Consider supplementation or dietary changes")
        
        return insights

    def generate_recommendations(self, test_values: List[Dict]) -> List[Dict]:
        """Generate personalized health recommendations"""
        recommendations = []
        
        abnormalities = self.identify_abnormalities(test_values)
        
        if abnormalities:
            recommendations.append({
                'category': 'Diet',
                'items': [
                    'Increase intake of leafy greens and vegetables',
                    'Reduce processed foods and sugary drinks',
                    'Include omega-3 rich foods (fish, nuts)',
                    'Stay hydrated: 8-10 glasses of water daily'
                ]
            })
        else:
            recommendations.append({
                'category': 'Prevention',
                'items': [
                    'Maintain current healthy lifestyle',
                    'Continue regular exercise routine',
                    'Annual health checkups',
                    'Stay mentally and physically active'
                ]
            })
        
        return recommendations

    def generate_summary(self, health_score: float, risk_level: str) -> str:
        """Generate health summary text"""
        if risk_level == 'Low':
            return f"Your health metrics are good (Score: {health_score:.1f}/100). Maintain your current lifestyle."
        elif risk_level == 'Moderate':
            return f"Your health needs attention (Score: {health_score:.1f}/100). Consider lifestyle changes and consult your doctor."
        else:
            return f"Your health requires immediate attention (Score: {health_score:.1f}/100). Please consult a healthcare professional urgently."

    def categorize_tests(self, test_values: List[Dict]) -> Dict:
        """Organize tests by category"""
        categorized = {}
        
        for test in test_values:
            category = test.get('category', 'Other')
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(test)
        
        return categorized
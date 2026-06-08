from typing import List, Dict, Tuple
import json
from geopy.distance import geodesic

class HospitalRecommender:
    """AI-powered hospital and specialist recommendation system"""
    
    HOSPITALS_DB = [
        {
            'id': 1,
            'name': 'Apollo Hospitals',
            'city': 'Mumbai',
            'lat': 19.0176,
            'long': 72.8194,
            'specialties': ['Cardiology', 'Nephrology', 'Endocrinology', 'General Medicine'],
            'rating': 4.8,
            'beds': 600,
            'emergency': True,
            'accreditation': 'JCI'
        },
        {
            'id': 2,
            'name': 'Max Healthcare',
            'city': 'Delhi',
            'lat': 28.5355,
            'long': 77.2065,
            'specialties': ['Cardiology', 'Oncology', 'Orthopedics', 'Endocrinology'],
            'rating': 4.7,
            'beds': 500,
            'emergency': True,
            'accreditation': 'JCI'
        },
        {
            'id': 3,
            'name': 'Fortis Healthcare',
            'city': 'Bangalore',
            'lat': 12.9716,
            'long': 77.5946,
            'specialties': ['Nephrology', 'Cardiology', 'Thyroid', 'General Medicine'],
            'rating': 4.6,
            'beds': 400,
            'emergency': True,
            'accreditation': 'NABH'
        }
    ]
    
    SPECIALTY_MAP = {
        'hemoglobin': 'Hematology',
        'blood_sugar': 'Endocrinology',
        'cholesterol': 'Cardiology',
    }

    def recommend_hospitals(self, abnormalities: List[Dict], user_location: Tuple[float, float] = None) -> List[Dict]:
        """Recommend hospitals based on abnormalities"""
        
        if not abnormalities:
            return self.get_general_hospitals(user_location)
        
        required_specialties = self.determine_specialties(abnormalities)
        
        hospital_scores = []
        for hospital in self.HOSPITALS_DB:
            score = self.calculate_hospital_score(
                hospital,
                required_specialties,
                user_location
            )
            hospital_scores.append({
                'hospital': hospital,
                'score': score,
                'matching_specialties': self.get_matching_specialties(hospital, required_specialties)
            })
        
        hospital_scores.sort(key=lambda x: x['score'], reverse=True)
        
        return [
            {
                'rank': i + 1,
                'name': h['hospital']['name'],
                'city': h['hospital']['city'],
                'specialties': h['matching_specialties'],
                'rating': h['hospital']['rating'],
                'beds': h['hospital']['beds'],
                'emergency_available': h['hospital']['emergency'],
                'accreditation': h['hospital']['accreditation'],
                'score': round(h['score'], 2),
                'recommended_for': self.get_recommendation_reason(abnormalities)
            }
            for i, h in enumerate(hospital_scores[:5])
        ]

    def determine_specialties(self, abnormalities: List[Dict]) -> List[str]:
        """Determine required specialties"""
        specialties = set()
        
        for abnormality in abnormalities:
            test_name = abnormality['test_name'].lower().replace(' ', '_')
            
            for key, specialty in self.SPECIALTY_MAP.items():
                if key in test_name or test_name in key:
                    specialties.add(specialty)
                    break
        
        if not specialties:
            specialties.add('General Medicine')
        
        return list(specialties)

    def calculate_hospital_score(self, hospital: Dict, required_specialties: List[str], user_location: Tuple[float, float] = None) -> float:
        """Calculate hospital suitability score"""
        score = 0
        
        score += hospital['rating'] * 3
        
        matching_specialties = self.get_matching_specialties(hospital, required_specialties)
        specialty_match_percentage = (len(matching_specialties) / len(required_specialties)) * 100 if required_specialties else 0
        score += (specialty_match_percentage / 100) * 40
        
        if hospital['accreditation'] == 'JCI':
            score += 20
        elif hospital['accreditation'] == 'NABH':
            score += 15
        else:
            score += 10
        
        if user_location:
            distance = self.calculate_distance(user_location, (hospital['lat'], hospital['long']))
            distance_score = max(0, 10 - (distance / 100))
            score += distance_score
        else:
            score += 10
        
        return score

    def get_matching_specialties(self, hospital: Dict, required_specialties: List[str]) -> List[str]:
        """Get matching specialties"""
        hospital_specialties = set(hospital['specialties'])
        required_set = set(required_specialties)
        return list(hospital_specialties.intersection(required_set))

    def get_general_hospitals(self, user_location: Tuple[float, float] = None) -> List[Dict]:
        """Get top general hospitals"""
        recommendations = []
        
        hospital_scores = []
        for hospital in self.HOSPITALS_DB:
            score = hospital['rating'] * 20
            if user_location:
                distance = self.calculate_distance(user_location, (hospital['lat'], hospital['long']))
                score -= distance / 50
            hospital_scores.append((hospital, score))
        
        hospital_scores.sort(key=lambda x: x[1], reverse=True)
        
        for i, (hospital, _) in enumerate(hospital_scores[:3]):
            recommendations.append({
                'rank': i + 1,
                'name': hospital['name'],
                'city': hospital['city'],
                'specialties': hospital['specialties'],
                'rating': hospital['rating'],
                'beds': hospital['beds'],
                'emergency_available': hospital['emergency'],
                'accreditation': hospital['accreditation'],
                'recommended_for': 'General Health Checkup'
            })
        
        return recommendations

    @staticmethod
    def calculate_distance(loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """Calculate distance between two locations"""
        try:
            return geodesic(loc1, loc2).kilometers
        except:
            return 0

    @staticmethod
    def get_recommendation_reason(abnormalities: List[Dict]) -> str:
        """Generate recommendation reason"""
        if not abnormalities:
            return "Routine checkup and preventive care"
        
        severity_count = len(abnormalities)
        
        if severity_count == 1:
            return f"Follow-up for {abnormalities[0]['test_name']}"
        else:
            return f"Comprehensive checkup for {severity_count} abnormal values"
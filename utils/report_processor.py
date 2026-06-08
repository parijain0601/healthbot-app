import os
import re
import json
from typing import Dict, List, Tuple
import pytesseract
from PIL import Image
import PyPDF2
import requests
from datetime import datetime

class ReportProcessor:
    """Advanced medical report processor with OCR and PDF extraction"""
    
    # Medical test patterns and reference ranges
    MEDICAL_TESTS = {
        'hemoglobin': {
            'patterns': [r'hemoglobin', r'hb', r'hgb'],
            'unit': 'g/dL',
            'reference': {'min': 12.0, 'max': 17.5},
            'category': 'Blood'
        },
        'blood_sugar': {
            'patterns': [r'blood\s*sugar', r'glucose', r'fbs', r'random\s*blood\s*sugar'],
            'unit': 'mg/dL',
            'reference': {'min': 70, 'max': 100},
            'category': 'Metabolic'
        },
        'cholesterol': {
            'patterns': [r'total\s*cholesterol', r'cholesterol(?!\s*hdl|\s*ldl)'],
            'unit': 'mg/dL',
            'reference': {'min': 0, 'max': 200},
            'category': 'Lipid'
        },
        'ldl': {
            'patterns': [r'ldl', r'low\s*density', r'bad\s*cholesterol'],
            'unit': 'mg/dL',
            'reference': {'min': 0, 'max': 100},
            'category': 'Lipid'
        },
        'hdl': {
            'patterns': [r'hdl', r'high\s*density', r'good\s*cholesterol'],
            'unit': 'mg/dL',
            'reference': {'min': 40, 'max': 1000},
            'category': 'Lipid'
        },
        'triglycerides': {
            'patterns': [r'triglycerides', r'trg'],
            'unit': 'mg/dL',
            'reference': {'min': 0, 'max': 150},
            'category': 'Lipid'
        },
        'vitamin_d': {
            'patterns': [r'vitamin\s*d', r'vit\s*d', r'25-oh\s*vitamin\s*d'],
            'unit': 'ng/mL',
            'reference': {'min': 30, 'max': 100},
            'category': 'Vitamin'
        },
        'vitamin_b12': {
            'patterns': [r'vitamin\s*b12', r'vit\s*b12', r'cobalamin'],
            'unit': 'pg/mL',
            'reference': {'min': 200, 'max': 900},
            'category': 'Vitamin'
        }
    }

    @staticmethod
    def extract_from_pdf(file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except Exception as e:
            print(f"Error extracting PDF: {e}")
            return ""

    @staticmethod
    def extract_from_image(file_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting image: {e}")
            return ""

    @staticmethod
    def extract_from_text(file_path: str) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""

    def process_report(self, file_path: str) -> Dict:
        """Process report and extract medical data"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            raw_text = self.extract_from_pdf(file_path)
        elif file_ext in ['.jpg', '.jpeg', '.png']:
            raw_text = self.extract_from_image(file_path)
        else:
            raw_text = self.extract_from_text(file_path)
        
        if not raw_text:
            return {'error': 'Could not extract text from file'}
        
        test_values = self.parse_medical_values(raw_text)
        
        return {
            'raw_text': raw_text,
            'test_values': test_values,
            'processed_at': datetime.utcnow().isoformat()
        }

    def parse_medical_values(self, text: str) -> List[Dict]:
        """Extract medical test values from text"""
        test_values = []
        text_lower = text.lower()
        
        for test_name, test_config in self.MEDICAL_TESTS.items():
            for pattern in test_config['patterns']:
                if re.search(pattern, text_lower):
                    value = self.extract_value_near_test(text, pattern)
                    
                    if value is not None:
                        status = self.determine_status(
                            value,
                            test_config['reference']
                        )
                        
                        test_values.append({
                            'test_name': test_name.replace('_', ' ').title(),
                            'value': value,
                            'unit': test_config['unit'],
                            'reference_range': f"{test_config['reference']['min']}-{test_config['reference']['max']}",
                            'status': status,
                            'category': test_config['category']
                        })
                    break
        
        return test_values

    @staticmethod
    def extract_value_near_test(text: str, pattern: str, window: int = 50) -> float:
        """Extract numeric value near test name"""
        try:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                return None
            
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            window_text = text[start:end]
            
            numbers = re.findall(r'\d+\.?\d*', window_text)
            
            if numbers:
                return float(numbers[-1])
        except Exception as e:
            print(f"Error extracting value: {e}")
        
        return None

    @staticmethod
    def determine_status(value: float, reference_range: Dict) -> str:
        """Determine if value is low, normal, or high"""
        if value < reference_range['min']:
            return 'Low'
        elif value > reference_range['max']:
            return 'High'
        else:
            return 'Normal'
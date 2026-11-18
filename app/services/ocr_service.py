import os
import re
try:
    import cv2
    import numpy as np
    HAS_OPENCV = True
except Exception as e:
    HAS_OPENCV = False
    cv2 = None
    np = None
from PIL import Image
import pytesseract
from flask import current_app
from app.extensions import db
from app.models.document import UploadedDocument

class OCRService:
    @staticmethod
    def _preprocess_image(image_path):
        """
        Enhance image contrast and remove noise using OpenCV prior to OCR.
        Falls back to PIL image opening if OpenCV is unavailable.
        """
        if not HAS_OPENCV or cv2 is None:
            return Image.open(image_path)
        try:
            img = cv2.imread(image_path)
            if img is None:
                return Image.open(image_path)
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Denoise using bilateral filter to keep sharp edges
            denoised = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert OpenCV ndarray back to PIL Image
            return Image.fromarray(thresh)
        except Exception as e:
            print(f"[OCR Preprocessing Warning] OpenCV fallback to direct PIL: {e}")
            return Image.open(image_path)

    @staticmethod
    def extract_text_from_file(file_path):
        """
        Extract textual content using Tesseract OCR, with robust fallback for PDFs and images.
        """
        if not os.path.exists(file_path):
            return "", "File not found on server disk."
        
        ext = file_path.rsplit('.', 1)[-1].lower()
        extracted_text = ""
        
        # Configure tesseract binary path if configured
        tesseract_cmd = current_app.config.get('TESSERACT_CMD')
        if tesseract_cmd and os.path.exists(tesseract_cmd):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        
        try:
            if ext in ('jpg', 'jpeg', 'png'):
                processed_img = OCRService._preprocess_image(file_path)
                try:
                    extracted_text = pytesseract.image_to_string(processed_img)
                except Exception as t_err:
                    # In environments without Tesseract binary installed
                    return "", f"Tesseract engine not accessible: {t_err}"
            elif ext == 'pdf':
                # Read text stream from PDF if present (via PyPDF)
                try:
                    import pypdf
                    reader = pypdf.PdfReader(file_path)
                    pages_text = []
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            pages_text.append(t)
                    extracted_text = "\n".join(pages_text)
                except Exception as pdf_err:
                    return "", f"PDF parsing error: {pdf_err}"
            
            return extracted_text.strip(), None
        except Exception as e:
            return "", str(e)

    @staticmethod
    def parse_document_entities(text):
        """
        Extract structured entities: Staff numbers, Dates, Ministries, Names from extracted text.
        """
        entities = {
            'staff_numbers': [],
            'dates': [],
            'names_found': [],
            'ministries_found': []
        }
        
        if not text:
            return entities
        
        # Match Nigerian Staff number patterns e.g. FGN/EDU/2018/00125 or P14258 or GL/2020/...
        staff_pattern = r'\b([A-Z]{2,4}\/[A-Z0-9]{2,6}\/\d{4}\/\d{3,6})\b|\b([A-Z]{2,4}\/\d{4}\/\d{3,6})\b'
        staff_matches = re.findall(staff_pattern, text)
        for match in staff_matches:
            val = match[0] or match[1]
            if val and val not in entities['staff_numbers']:
                entities['staff_numbers'].append(val)
        
        # Match dates in DD/MM/YYYY, DD-MM-YYYY, or YYYY-MM-DD
        date_pattern = r'\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b|\b(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})\b'
        date_matches = re.findall(date_pattern, text)
        for match in date_matches:
            val = match[0] or match[1]
            if val and val not in entities['dates']:
                entities['dates'].append(val)
        
        # Match common Nigerian Ministries
        ministry_keywords = [
            'Ministry of Education', 'Ministry of Health', 'Ministry of Finance',
            'Ministry of Works', 'Ministry of Agriculture', 'Ministry of Justice',
            'Office of the Head of Civil Service', 'Federal Civil Service Commission'
        ]
        for min_name in ministry_keywords:
            if re.search(re.escape(min_name), text, re.IGNORECASE):
                entities['ministries_found'].append(min_name)
        
        return entities

    @staticmethod
    def compare_with_employee_record(entities, raw_text, employee):
        """
        Compare OCR entities against the official employee database record.
        """
        results = {
            'staff_no_match': 'Not Found in Document',
            'name_match': 'Not Found in Document',
            'inconsistencies': []
        }
        
        # Check Staff Number
        emp_staff_clean = employee.staff_number.strip().upper()
        if any(emp_staff_clean in s.upper() for s in entities.get('staff_numbers', [])) or emp_staff_clean in raw_text.upper():
            results['staff_no_match'] = 'Exact Match'
        elif entities.get('staff_numbers'):
            other_staff = entities['staff_numbers'][0]
            results['staff_no_match'] = f'Discrepancy (Extracted: {other_staff})'
            results['inconsistencies'].append(f"Document contains staff number '{other_staff}' which does not match registered '{employee.staff_number}'.")
        
        # Check Employee Name (first and last name)
        first_clean = employee.first_name.strip().upper()
        last_clean = employee.last_name.strip().upper()
        
        raw_upper = raw_text.upper()
        if first_clean in raw_upper and last_clean in raw_upper:
            results['name_match'] = 'Full Name Match'
        elif first_clean in raw_upper or last_clean in raw_upper:
            results['name_match'] = 'Partial Name Match'
            results['inconsistencies'].append(f"Only partial name match found in document text.")
        else:
            results['name_match'] = 'Name Not Detected in Text'
            
        return results

    @staticmethod
    def process_document(document_id, employee):
        """
        Run OCR pipeline on a specific document, store text and metadata.
        """
        doc = UploadedDocument.query.get(document_id)
        if not doc:
            return None, "Document not found."
        
        text, error = OCRService.extract_text_from_file(doc.file_path)
        if error:
            doc.ocr_status = 'manual_review'
            doc.extracted_text = f"[OCR Notice: Extraction engine flagged for manual officer inspection. Note: {error}]"
            doc.extracted_metadata = {'error': error, 'requires_manual_inspection': True}
            db.session.commit()
            return doc, error
        
        entities = OCRService.parse_document_entities(text)
        comparison = OCRService.compare_with_employee_record(entities, text, employee)
        
        doc.ocr_status = 'processed'
        doc.extracted_text = text
        doc.extracted_metadata = {
            'entities': entities,
            'comparison': comparison,
            'character_count': len(text)
        }
        db.session.commit()
        return doc, None

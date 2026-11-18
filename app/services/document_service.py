import os
import hashlib
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.extensions import db
from app.models.document import UploadedDocument, DocumentType

MAGIC_BYTES = {
    'pdf': b'%PDF-',
    'png': b'\x89PNG\r\n\x1a\n',
    'jpg': b'\xff\xd8\xff',
    'jpeg': b'\xff\xd8\xff'
}

class DocumentService:
    @staticmethod
    def is_allowed_file(filename):
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in current_app.config.get('ALLOWED_EXTENSIONS', {'pdf', 'png', 'jpg', 'jpeg'})

    @staticmethod
    def validate_file_content(file_storage, ext):
        """Verify the initial header bytes match the expected format."""
        pos = file_storage.tell()
        file_storage.seek(0)
        header = file_storage.read(16)
        file_storage.seek(pos)
        
        expected = MAGIC_BYTES.get(ext)
        if not expected:
            return True
        if ext in ('jpg', 'jpeg'):
            return header.startswith(b'\xff\xd8')
        return header.startswith(expected[:len(expected)])

    @staticmethod
    def save_document(file_storage, application_id, document_type, user_id=None):
        """
        Securely store an uploaded document and create database record.
        """
        if not file_storage or not file_storage.filename:
            return None, "No file selected."
        
        orig_filename = secure_filename(file_storage.filename)
        if not DocumentService.is_allowed_file(orig_filename):
            return None, "File extension is not permitted. Only PDF, PNG, and JPG/JPEG files are allowed."
        
        ext = orig_filename.rsplit('.', 1)[1].lower()
        if not DocumentService.validate_file_content(file_storage, ext):
            return None, "File content signature does not match the file extension."
        
        # Calculate SHA256 hash and file size
        file_storage.seek(0)
        hasher = hashlib.sha256()
        size = 0
        while chunk := file_storage.read(65536):
            hasher.update(chunk)
            size += len(chunk)
        sha256_hash = hasher.hexdigest()
        file_storage.seek(0)
        
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        if size > max_size:
            return None, f"File size exceeds maximum permitted limit of {max_size // (1024*1024)}MB."

        # Generate unique storage filename
        stored_filename = f"app_{application_id}_{document_type}_{uuid.uuid4().hex[:12]}.{ext}"
        upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, stored_filename)
        
        file_storage.save(file_path)
        
        mime_type = file_storage.content_type or f"application/{ext}"
        
        # Create record
        doc = UploadedDocument(
            application_id=application_id,
            document_type=document_type,
            original_filename=orig_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_size_bytes=size,
            mime_type=mime_type,
            sha256_hash=sha256_hash,
            ocr_status='pending'
        )
        db.session.add(doc)
        db.session.commit()
        
        return doc, None

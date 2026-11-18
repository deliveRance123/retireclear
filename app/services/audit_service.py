from flask import request
from flask_login import current_user
from app.extensions import db
from app.models.audit import AuditLog

class AuditService:
    @staticmethod
    def log(action, target_model=None, target_id=None, details=None, user_id=None):
        """
        Record an immutable entry in the audit log table.
        """
        try:
            effective_user_id = user_id
            if effective_user_id is None and current_user and current_user.is_authenticated:
                effective_user_id = current_user.id
            
            ip_address = None
            user_agent = None
            if request:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                if ip_address and ',' in ip_address:
                    ip_address = ip_address.split(',')[0].strip()
                user_agent = request.user_agent.string[:250] if request.user_agent else None
            
            log_entry = AuditLog(
                user_id=effective_user_id,
                action=action,
                target_model=target_model,
                target_id=target_id,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details or {}
            )
            db.session.add(log_entry)
            db.session.commit()
            return log_entry
        except Exception as e:
            db.session.rollback()
            print(f"[AuditService Error] Failed to write audit log: {e}")
            return None

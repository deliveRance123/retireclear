from datetime import datetime
from app.extensions import db

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(80), unique=True, nullable=False, index=True)
    setting_value = db.Column(db.Text, nullable=False)
    setting_type = db.Column(db.String(20), default='string')  # string, integer, float, boolean, json
    description = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get_value(cls, key, default=None):
        setting = cls.query.filter_by(setting_key=key).first()
        if not setting:
            return default
        
        val = setting.setting_value
        if setting.setting_type == 'integer':
            return int(val)
        elif setting.setting_type == 'float':
            return float(val)
        elif setting.setting_type == 'boolean':
            return val.lower() in ('true', '1', 'yes')
        return val

    @classmethod
    def set_value(cls, key, value, description=None, setting_type='string'):
        setting = cls.query.filter_by(setting_key=key).first()
        if not setting:
            setting = cls(setting_key=key, setting_value=str(value), description=description, setting_type=setting_type)
            db.session.add(setting)
        else:
            setting.setting_value = str(value)
            if description:
                setting.description = description
            if setting_type:
                setting.setting_type = setting_type
        db.session.commit()
        return setting

    def __repr__(self):
        return f'<SystemSetting {self.setting_key}={self.setting_value}>'

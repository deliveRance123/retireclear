import os
from flask import current_app

class BiometricService:
    @staticmethod
    def get_biometric_status(employee):
        """
        Assess biometric readiness truthfully based on physical hardware
        and enrolled civil service biometric templates.
        """
        hardware_available = current_app.config.get('BIOMETRIC_HARDWARE_ENABLED', False)
        
        if not hardware_available:
            return {
                'hardware_connected': False,
                'status_label': 'Not Configured (Hardware Required)',
                'facial_recognition_ready': False,
                'fingerprint_scanner_ready': False,
                'enrolled_in_database': bool(employee.biometric_enrolled),
                'message': (
                    'Biometric capture hardware (optical fingerprint reader / calibrated camera) '
                    'is not connected to this terminal. Manual civil service document review is authorized.'
                ),
                'requires_manual_waiver': True
            }
        
        # If hardware is present in production environment
        return {
            'hardware_connected': True,
            'status_label': 'Enrolled Reference Ready' if employee.biometric_enrolled else 'Pending Enrolment',
            'facial_recognition_ready': True,
            'fingerprint_scanner_ready': True,
            'enrolled_in_database': bool(employee.biometric_enrolled),
            'message': 'Hardware terminal online. Ready for live biometric matching.',
            'requires_manual_waiver': not employee.biometric_enrolled
        }

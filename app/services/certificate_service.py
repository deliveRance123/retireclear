import os
import uuid
import qrcode
from datetime import datetime
from flask import current_app, url_for
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from app.extensions import db
from app.models.clearance import RetirementCertificate

class CertificateService:
    @staticmethod
    def generate_certificate(clearance, is_sample=True):
        """
        Create certificate database record, generate QR code, and build printable PDF.
        """
        app_obj = clearance.application
        emp = app_obj.employee
        
        # Check if already generated
        existing = RetirementCertificate.query.filter_by(clearance_id=clearance.id).first()
        if existing:
            return existing
            
        cert_number = f"FGN-RET-CERT-{datetime.utcnow().year}-{clearance.id:05d}"
        token = uuid.uuid4().hex
        
        cert_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'certificates')
        os.makedirs(cert_dir, exist_ok=True)
        
        # 1. Generate QR Code
        # Points to the public verification route
        verify_url = f"/certificates/verify/{token}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=6,
            border=2,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="#174C3C", back_color="white")
        qr_filename = f"qr_{token[:12]}.png"
        qr_path = os.path.join(cert_dir, qr_filename)
        qr_img.save(qr_path)
        
        # 2. Build PDF Certificate using ReportLab
        pdf_filename = f"certificate_{cert_number.replace('-', '_')}.pdf"
        pdf_path = os.path.join(cert_dir, pdf_filename)
        
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(letter),
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CertTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            alignment=1, # Center
            textColor=colors.HexColor('#174C3C')
        )
        
        sub_style = ParagraphStyle(
            'CertSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            alignment=1,
            textColor=colors.HexColor('#C87959')
        )
        
        header_fed = ParagraphStyle(
            'CertFed',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            alignment=1,
            textColor=colors.HexColor('#10382E')
        )

        watermark_style = ParagraphStyle(
            'Watermark',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=14,
            alignment=1,
            textColor=colors.HexColor('#C94D4D')
        )
        
        body_style = ParagraphStyle(
            'CertBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=16,
            alignment=1,
            textColor=colors.HexColor('#252C28')
        )
        
        story = []
        
        story.append(Paragraph("FEDERAL REPUBLIC OF NIGERIA", header_fed))
        story.append(Paragraph("OFFICE OF THE HEAD OF THE CIVIL SERVICE OF THE FEDERATION", sub_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph("NATIONAL RETIREMENT CLEARANCE CERTIFICATE", title_style))
        if is_sample:
            story.append(Spacer(1, 4))
            story.append(Paragraph("--- OFFICIAL DEMONSTRATION / SAMPLE CERTIFICATE ---", watermark_style))
        
        story.append(Spacer(1, 15))
        
        cert_text = (
            f"This is to certify that <b>{emp.full_name.upper()}</b> (Staff No: <b>{emp.staff_number}</b>), "
            f"formerly serving in the <b>{emp.ministry_or_agency}</b> (Department of {emp.department}) "
            f"at Grade Level <b>{emp.current_grade_level}</b>, has satisfactorily fulfilled all statutory service records, "
            f"audit obligations, and pension clearance requirements in accordance with Public Service Rules."
        )
        story.append(Paragraph(cert_text, body_style))
        story.append(Spacer(1, 15))
        
        # Details Table
        data = [
            [
                Paragraph(f"<b>Certificate Number:</b> {cert_number}", styles['Normal']),
                Paragraph(f"<b>Effective Retirement Date:</b> {app_obj.proposed_retirement_date.strftime('%d/%m/%Y')}", styles['Normal'])
            ],
            [
                Paragraph(f"<b>Years of Service:</b> {emp.years_of_service} Years", styles['Normal']),
                Paragraph(f"<b>Date of First Appointment:</b> {emp.appointment_date.strftime('%d/%m/%Y')}", styles['Normal'])
            ],
            [
                Paragraph(f"<b>Clearance Decision:</b> {clearance.decision}", styles['Normal']),
                Paragraph(f"<b>Approval Date:</b> {clearance.decision_date.strftime('%d/%m/%Y')}", styles['Normal'])
            ],
            [
                Paragraph(f"<b>Authorizing Pension Officer:</b> {clearance.approving_officer.full_name}", styles['Normal']),
                Paragraph(f"<b>Verification Token:</b> {token[:16]}...", styles['Normal'])
            ]
        ]
        
        t = Table(data, colWidths=[330, 330])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F7F2')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#174C3C')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DCE8DF')),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))
        
        # Sign-off & QR Row
        qr_element = RLImage(qr_path, width=65, height=65)
        sign_table_data = [
            [
                qr_element,
                Paragraph("<b>Scan QR to Verify Authenticity Online</b><br/><font size='8' color='#778079'>National Retirement Clearance Portal • FGN Verifiable Document Security Framework</font>", styles['Normal']),
                Paragraph("________________________________<br/><b>Permanent Secretary / Director-General</b><br/><font size='8' color='#778079'>Federal Civil Service Commission</font>", styles['Normal'])
            ]
        ]
        sign_table = Table(sign_table_data, colWidths=[80, 340, 240])
        sign_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (2,0), (2,0), 'CENTER'),
        ]))
        story.append(sign_table)
        
        doc.build(story)
        
        # Create database record
        cert = RetirementCertificate(
            certificate_number=cert_number,
            clearance_id=clearance.id,
            application_id=app_obj.id,
            employee_id=emp.id,
            verification_token=token,
            qr_code_path=f"certificates/{qr_filename}",
            pdf_path=f"certificates/{pdf_filename}",
            is_sample=is_sample
        )
        db.session.add(cert)
        db.session.commit()
        
        return cert

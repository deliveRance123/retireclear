# AI-Integrated Automated Retirement Clearance and Verification System for Civil Servants (Nigeria)

> **National Retirement Clearance Portal**  
> *Federal Republic of Nigeria — AI-Integrated Public Sector Verification Platform*

---

## 1. System Overview

The **National Retirement Clearance Portal** is an enterprise-grade digital public administration system designed specifically to automate, standardize, and verify retirement clearance processes across Nigerian Federal and State Ministries, Departments, and Agencies (MDAs).

The system coordinates civil service record reconciliation, automated optical character recognition (OCR) parsing of statutory service documents (via Tesseract & OpenCV), rule-based eligibility evaluation, anomaly detection for duplicate records, and role-based clearance approval across five distinct tiers. **Crucially, AI acts exclusively as an auditable decision-support engine—authorized human officers retain exclusive legal clearance authority.**

---

## 2. Technology Stack

- **Backend:** Python 3.12+ / Flask (Application Factory & Blueprints modular architecture)
- **Database:** MySQL 8.0+ / MariaDB (InnoDB engine, utf8mb4 character set, parameterized ORM queries, foreign key cascades, and unique indexes)
- **ORM & Migrations:** Flask-SQLAlchemy 3.1+, Flask-Migrate 4.1+ (Alembic)
- **Authentication & Security:** Flask-Login, Flask-WTF (CSRF protection), Werkzeug password hashing, session throttling, and brute-force lockout
- **Frontend:** HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons, Chart.js 4.4, Jinja2 template inheritance
- **AI & Document Processing:** 
  - **Tesseract OCR:** Text stream extraction from uploaded service records
  - **OpenCV (`cv2`):** Grayscale conversion, bilateral filtering, and adaptive Gaussian thresholding for enhanced document clarity
  - **Scikit-learn:** Data preprocessing & anomaly detection heuristics
  - **Rule-Based Expert Engine:** Configurable public service retirement eligibility assessment
- **Reporting & Issuance:** 
  - **ReportLab:** Cryptographic PDF generation for official Retirement Clearance Certificates
  - **QRCode:** Digital verification token generation for public authenticity checks

---

## 3. Nigerian Visual Identity & Design System

The portal strictly implements the official public-sector visual identity without any blue elements:

| Token | Hex Code | Purpose in Interface |
| :--- | :--- | :--- |
| **Deep Forest Green** | `#174C3C` | Primary brand identity, headers, main action buttons |
| **Dark Evergreen** | `#10382E` | Sidebar navigation, dark container backgrounds |
| **Warm Ivory** | `#F8F7F2` | Main page canvas and background surfaces |
| **Pure White** | `#FFFFFF` | Cards, elevated surfaces, and form containers |
| **Muted Sage** | `#DCE8DF` | Subtle dividers, borders, and card outlines |
| **Terracotta** | `#C87959` | Secondary accent, caution badges, flagged alert tags |
| **Soft Gold** | `#C6A15B` | Seals, emblems, certificate borders, and highlights |
| **Charcoal** | `#252C28` | Primary high-contrast readable body text |
| **Muted Grey** | `#778079` | Secondary metadata labels and captions |
| **Success Green** | `#258451` | Approved clearance badges and success toasts |
| **Warning Amber** | `#D99A32` | In-progress workflow and pending indicators |
| **Error Red** | `#C94D4D` | Rejected decisions and high-risk fraud alerts |

---

## 4. Role-Based Access Control (5 System Roles)

1. **System Administrator (`admin`):** System governance, user provisioning, role assignments, configurable eligibility rule tuning, database integrity, and system audit logs.
2. **Human Resource Officer (`hr_officer`):** Employee onboarding, service record books, gazetted promotions, tenure calculations, and initial service verification.
3. **Pension Officer (`pension_officer`):** Pension Board adjudication, PenCom RSA coordination, clearance approvals/rejections, and certificate issuance.
4. **Independent Auditor (`auditor`):** Irregularity investigations, duplicate record detection, identity conflict inquiries, and audit trail oversight.
5. **Retiring Civil Servant (`civil_servant`):** Self-service clearance initiation, statutory document uploads, real-time workflow tracking, and certificate downloads.

---

## 5. Local Setup & Installation Instructions

### Prerequisites
- Python 3.12+ (or compatible 3.13/3.14)
- MySQL Server 8.0+ or XAMPP (Apache + MySQL)
- Git

### Step 1: Clone or Navigate to Project
```bash
cd c:\rcssystem
```

### Step 2: Configure Environment Variables
Copy `.env.example` to `.env` and verify database credentials:
```ini
SECRET_KEY=nigerian-civil-service-secure-key-2026-fgn-ret
FLASK_ENV=development
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=retirement_clearance_db
```

### Step 3: Create MySQL Database
Using the MySQL command line or XAMPP phpMyAdmin:
```sql
CREATE DATABASE IF NOT EXISTS retirement_clearance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
*(Alternatively, import `schema.sql` directly).*

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Seed Database with Realistic Demo Data
Run the seeder script to populate roles, configurable rules, and realistic Nigerian public servants:
```bash
python seed_db.py
```

### Step 6: Start Application Server
```bash
python run.py
```
Open your browser at `http://127.0.0.1:5000`.

---

## 6. Demonstration Accounts (Fictional Demo Data)

| Role | Username | Password | Full Name & MDA |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin` | `AdminPass@2026` | Ibrahim Danjuma (FCSC) |
| **HR Officer** | `hr_officer` | `HrPass@2026` | Folashade Adeyemi (Ministry of Education) |
| **Pension Officer** | `pension_officer` | `PensionPass@2026` | Emeka Okafor (PenCom Desk) |
| **Auditor** | `auditor` | `AuditorPass@2026` | Amina Mohammed (Audit Directorate) |
| **Retiring Civil Servant** | `adebayo.olumide` | `RetireePass@2026` | Adebayo Olumide (GL 14, Min of Education) |

*All demonstration records are fictional and clearly marked as sample data.*

---

## 7. Automated Testing Suite

Execute the comprehensive test suite with pytest:
```bash
python -m pytest -v tests/
```
The suite verifies:
- Authentication & lockout protection
- Nigerian phone and staff number validation
- Rule-based eligibility thresholds (60 years age / 35 years service / configurable operators)
- Anomaly and duplicate record detection
- Full clearance approval workflow and certificate generation
- Public verification endpoint privacy (hiding private contact and NIN data)

---

## 8. Railway & Production Cloud Deployment

### 1. Build & Serve Configuration
- `Procfile` is preconfigured for production:
  ```
  web: gunicorn wsgi:app --workers 3 --timeout 120 --access-logfile - --error-logfile -
  ```
- `runtime.txt` specifies Python 3.12.

### 2. Railway Deployment Steps
1. Push the repository to GitHub.
2. In Railway Dashboard, create a **New Project** from the GitHub repository.
3. Provision a **MySQL Database** plugin in Railway.
4. Set Railway Environment Variables:
   - `DATABASE_URL`: Set automatically by Railway MySQL (`mysql://...`)
   - `SECRET_KEY`: Set a secure random string
   - `FLASK_CONFIG`: `production`
5. Deploy. The health check endpoint is available at `/health`.

---

## 9. Security & Compliance Architecture

- **Role-Based Guards:** All routes are protected by `@login_required` and `@role_required(...)` decorators.
- **CSRF Tokens:** All form submissions are protected via Flask-WTF.
- **File Validation:** Magic bytes inspection prevents malicious executable uploads masquerading as PDF or JPEG.
- **Private Storage:** Document files are stored outside web roots and served only via authenticated routes.
- **Immutable Audit Logging:** Captures user identity, IP address, target entity, timestamp, and metadata for every state modification.

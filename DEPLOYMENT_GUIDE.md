# Production Deployment Guide — RetireClear Portal
**AI-Integrated Automated Retirement Clearance and Verification System**

This guide provides step-by-step instructions for deploying the **RetireClear** portal to production.

---

## Pre-Deployment Checklist

Before deploying, ensure you have:
1. A **GitHub** account (for version control and automatic deployment).
2. Git installed locally on your computer.
3. Decided on your hosting platform:
   - **Railway.app** *(Recommended — easiest, provides managed MySQL & Python with zero server setup)*
   - **Render.com** *(Alternative cloud platform)*
   - **Linux VPS (Ubuntu / Debian)** *(For self-hosted or dedicated government cloud environments)*

---

## Method 1: Deploy to Railway (Recommended — 5 Minutes)

Railway provides native support for Python, Flask, Gunicorn, and managed MySQL databases.

### Step 1: Push Your Code to GitHub

Open PowerShell in the project directory (`C:\rcssystem`) and run:

```powershell
# 1. Initialize git
git init

# 2. Add all project files
git add .

# 3. Create initial commit
git commit -m "Release: RetireClear Production Application"

# 4. Link your remote GitHub repository (replace with your GitHub URL)
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git

# 5. Push to GitHub
git push -u origin main
```

---

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. Click **"New Project"** $\rightarrow$ **"Deploy from GitHub repo"**.
3. Select your repository.
4. In the same project canvas, click **"New"** $\rightarrow$ **"Database"** $\rightarrow$ **"Add MySQL"**.
5. Once the MySQL service is created, click on your Python web service $\rightarrow$ **Variables**:
   - Add a reference variable:
     - Name: `DATABASE_URL`
     - Value: Select `${{ MySQL.DATABASE_URL }}` from the dropdown.
   - Add:
     - `SECRET_KEY`: Enter a random secure string (e.g., `fgn-prod-retireclear-key-2026-xyz`).
     - `FLASK_CONFIG`: `production`
6. Click on **Settings** $\rightarrow$ **Networking** $\rightarrow$ **Generate Domain**.
7. Railway will automatically build the container using `Procfile` / `railway.json` and start the server with Gunicorn.
8. On first startup, `wsgi.py` automatically initializes all database tables, roles, and configuration!

---

## Method 2: Deploy to a Linux VPS (Ubuntu 22.04 / 24.04)

For hosting on a dedicated Virtual Private Server (AWS EC2, DigitalOcean Droplet, Linode, Azure):

### Step 1: Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv mysql-server tesseract-ocr nginx git
```

### Step 2: Setup MySQL Database

```bash
sudo mysql -u root
```
Inside MySQL shell:
```sql
CREATE DATABASE retirement_clearance_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'retire_admin'@'localhost' IDENTIFIED BY 'StrongPassword@2026';
GRANT ALL PRIVILEGES ON retirement_clearance_db.* TO 'retire_admin'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 3: Clone Code & Configure Environment

```bash
cd /var/www
sudo git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git rcssystem
cd rcssystem
sudo chown -R $USER:$USER /var/www/rcssystem

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn

# Create production .env file
cat <<EOF > .env
SECRET_KEY=fgn-prod-secure-token-2026
FLASK_CONFIG=production
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=retire_admin
MYSQL_PASSWORD=StrongPassword@2026
MYSQL_DATABASE=retirement_clearance_db
UPLOAD_FOLDER=/var/www/rcssystem/uploads
EOF

# Initialize database
python seed_db.py
```

### Step 4: Configure Gunicorn Systemd Service

Create `/etc/systemd/system/retireclear.service`:
```ini
[Unit]
Description=Gunicorn instance to serve RetireClear Portal
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/rcssystem
Environment="PATH=/var/www/rcssystem/venv/bin"
ExecStart=/var/www/rcssystem/venv/bin/gunicorn --workers 3 --bind unix:/var/www/rcssystem/retireclear.sock wsgi:app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start retireclear
sudo systemctl enable retireclear
```

### Step 5: Configure Nginx & SSL

Create `/etc/nginx/sites-available/retireclear`:
```nginx
server {
    listen 80;
    server_name yourdomain.gov.ng www.yourdomain.gov.ng;

    client_max_body_size 20M;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/rcssystem/retireclear.sock;
    }

    location /static {
        alias /var/www/rcssystem/app/static;
        expires 30d;
    }
}
```

Enable site and install free SSL certificate:
```bash
sudo ln -s /etc/nginx/sites-available/retireclear /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Install free Certbot SSL
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.gov.ng
```

---

## Method 3: Deploy via Docker Container

The repository includes a production-ready [Dockerfile](file:///c:/rcssystem/Dockerfile).

```bash
# Build the Docker image
docker build -t retireclear:latest .

# Run container with external MySQL connection
docker run -d -p 5000:5000 \
  -e SECRET_KEY="your-production-secret-key" \
  -e DATABASE_URL="mysql+pymysql://user:password@host:3306/retirement_clearance_db?charset=utf8mb4" \
  --name retireclear_app \
  retireclear:latest
```

---

## Default Administrative Accounts

Upon initial deployment and auto-seeding, the following accounts are ready:

| Role | Username | Password | Purpose |
| :--- | :--- | :--- | :--- |
| **System Administrator** | `admin` | `AdminPass@2026` | Full platform configuration, user roles, eligibility policies |
| **HR Officer** | `hr_officer` | `HrPass@2026` | Employee file verification, service tenure checking |
| **Pension Officer** | `pension_officer` | `PensionPass@2026` | Final retirement clearance adjudication & certificate generation |
| **Independent Auditor** | `auditor` | `AuditorPass@2026` | Forensic anomaly reviews, duplicate checking, integrity audits |
| **Retiring Civil Servant** | `adebayo.olumide` | `RetireePass@2026` | Self-service application tracking & certificate download |

> **Important:** Immediately log into the `admin` account in production to change the default passwords.

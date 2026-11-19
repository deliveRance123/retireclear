# Render Production Deployment Guide — RetireClear Portal
**AI-Integrated Automated Retirement Clearance and Verification System for Civil Servants**

This guide provides the simple, step-by-step instructions to deploy **RetireClear** to **Render** with **Neon Serverless PostgreSQL**.

---

## 1. Prerequisites

1. Your repository is on GitHub: [https://github.com/deliveRance123/retireclear](https://github.com/deliveRance123/retireclear)
2. Your Neon PostgreSQL Database URL:
   ```text
   postgresql://neondb_owner:npg_icZea7Rk8bfF@ep-winter-morning-bel94mhq-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

---

## 2. Deploying on Render (Step-by-Step)

### Option A: Standard Web Service (Recommended & Fastest)

1. Go to your [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** $\rightarrow$ select **Web Service**.
3. Select **Build and deploy from a Git repository** $\rightarrow$ click **Next**.
4. Connect or select your GitHub repository: **`deliveRance123/retireclear`** (branch: `main`).
5. Configure the service settings:
   - **Name**: `retireclear` (or any name you prefer)
   - **Region**: Closest to you (e.g., `Frankfurt` or `Oregon`)
   - **Branch**: `main`
   - **Root Directory**: *(leave blank)*
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn wsgi:app --bind 0.0.0.0:$PORT
     ```
   - **Instance Type**: `Free`

6. Scroll down to **Environment Variables** and add the following 3 variables:

   | Key | Value |
   | :--- | :--- |
   | `DATABASE_URL` | `postgresql://neondb_owner:npg_icZea7Rk8bfF@ep-winter-morning-bel94mhq-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require` |
   | `FLASK_CONFIG` | `production` |
   | `SECRET_KEY` | `nigerian-civil-service-secure-key-2026-fgn-ret` |
   | `PYTHON_VERSION` | `3.12.8` |

7. Click **Create Web Service**.

---

### Option B: Deploy via Blueprint (`render.yaml`)

Because the repository includes `render.yaml`:
1. In the Render Dashboard, click **New +** $\rightarrow$ **Blueprint**.
2. Select repository **`deliveRance123/retireclear`**.
3. Render will detect `render.yaml` automatically.
4. When prompted for environment variables, enter `DATABASE_URL`:
   ```text
   postgresql://neondb_owner:npg_icZea7Rk8bfF@ep-winter-morning-bel94mhq-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
5. Click **Apply**.

---

## 3. Why Render is More Reliable than Vercel for this Application

1. **Persistent WSGI Server**: Render runs Gunicorn continuously, avoiding cold boot timeouts and 250MB bundle size limits.
2. **Native PostgreSQL & Neon Compatibility**: Render containers have unrestricted outbound networking to Neon's pooled PostgreSQL servers.
3. **No Complex Internal Rewrites**: Standard HTTP routing to `wsgi:app` without serverless routing translation issues.
4. **Automatic Role Seeding**: The first time any visitor loads the home page, the database tables and user roles (`admin`, `hr_officer`, `pension_officer`, `auditor`, `civil_servant`) are automatically verified and seeded.

# Vercel Production Deployment Guide — RetireClear Portal
**National Automated Retirement Clearance and Verification System**

This guide provides the exact steps to deploy **RetireClear** to **Vercel** with **Neon Serverless PostgreSQL**.

---

## 1. Prerequisites

1. Your code is on GitHub: [https://github.com/deliveRance123/retireclear](https://github.com/deliveRance123/retireclear)
2. Your Neon PostgreSQL Database URL:
   ```text
   postgresql://neondb_owner:npg_icZea7Rk8bfF@ep-winter-morning-bel94mhq-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

---

## 2. Deploying on Vercel (3 Steps)

### Step 1: Import Project in Vercel
1. Log in to your [Vercel Dashboard](https://vercel.com/dashboard).
2. Click **"Add New..."** $\rightarrow$ **"Project"**.
3. Under *Import Git Repository*, find **`deliveRance123/retireclear`** and click **Import**.

### Step 2: Configure Environment Variables
Before clicking Deploy, expand the **Environment Variables** section and add the following 3 variables:

| Key | Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://neondb_owner:npg_icZea7Rk8bfF@ep-winter-morning-bel94mhq-pooler.c-9.us-east-2.aws.neon.tech/neondb?sslmode=require` | Connection to your Neon PostgreSQL cloud database |
| `SECRET_KEY` | `fgn-retireclear-production-key-2026-secure` | Application cryptographic session key |
| `FLASK_CONFIG` | `production` | Enables production mode with pooled database engine |

> **Important:** Do NOT wrap values in quotes when pasting them into the Vercel dashboard.

### Step 3: Deploy
1. Click **Deploy**.
2. Vercel will install dependencies via `@vercel/python`, configure the serverless function, and issue your live URL:
   `https://retireclear-xyz.vercel.app`

---

## 3. How the Architecture Works on Vercel

* **Entry Point:** `api/index.py` handles incoming HTTP requests as a Python WSGI Serverless Function.
* **Routing:** `vercel.json` rewrites all incoming traffic to `api/index.py`, allowing Flask to serve all pages and static assets seamlessly.
* **Database Resilience:** Database initialization is lazy (handled on the first web request via `@app.before_request`), preventing connection lockouts during Vercel's build phase.
* **File Uploads:** In serverless mode (`VERCEL=1`), temporary uploads are safely directed to `/tmp/uploads` to comply with read-only lambda filesystems.

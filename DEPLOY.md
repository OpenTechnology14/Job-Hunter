# Job Hunter — Local Setup & Deployment Guide

Two ways to run Job Hunter:
1. **Local** — on your own machine, everything stays on disk
2. **Hosted** — on a server, accessible by multiple users over the network

---

## Part 1: Local Setup (Your Machine)

### Prerequisites

| Requirement | Check | Install |
|-------------|-------|---------|
| Python 3.10+ | `python3 --version` | `brew install python@3.12` (Mac) or [python.org](https://python.org) |
| pip | `pip --version` | Comes with Python |
| Git (optional) | `git --version` | `brew install git` (Mac) or [git-scm.com](https://git-scm.com) |

### Step 1: Get the code

```bash
git clone https://github.com/YOUR_USERNAME/job-hunter.git
cd job-hunter
```

Or download and unzip the repo.

### Step 2: Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate          # Mac/Linux
# venv\Scripts\activate           # Windows
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 4: Create your profile

```bash
cp profiles/example_profile.py profiles/yourname.py
```

Edit `profiles/yourname.py` — fill in all sections:

```python
USER_PROFILE = {
    "name": "Your Name",
    "email": "you@email.com",
    "phone": "555-0100",
    "city": "Your City",
    "state": "ST",
    # ... skills, experience, etc.
}

ROLE_PROFILES = {
    "role_1": {
        "label": "Software Engineer",
        "search_queries": ["Software Engineer", "Backend Developer"],
        "salary_min": 80000,
        "salary_max": 150000,
        "resume_file": "software_engineer.pdf",
    },
    # Add more roles as needed
}

SEARCH_SETTINGS = {
    "locations": ["Remote", "Your City, ST"],
    "exclude_keywords": ["Senior", "Staff", "Principal"],
    "max_results_per_query": 25,
}

LOCATION_FILTER = {
    "city": "Your City",
    "state": "ST",
    "radius_miles": 30,
    "nearby_cities": ["Nearby Town"],
    "include_remote": True,
}

STORAGE_MODE = "local"   # or "google"
```

### Step 5: Add resumes

```bash
mkdir -p output/yourname/resumes
# Copy your PDF resumes into this folder
# Filenames must match resume_file values in ROLE_PROFILES
```

Verify:
```bash
python3 resume_picker.py --profile yourname
```

### Step 6: Set up environment file

```bash
cp .env.example .env
```

Edit `.env` — set `ACTIVE_PROFILE=yourname`. Add optional API keys.

### Step 7: First run

```bash
python3 run_scrape.py --profile yourname
```

Takes 1-3 minutes. Creates `output/yourname/jobs.csv`.

### Step 8: Verify

```bash
# Check CSV has results
head -5 output/yourname/jobs.csv

# Or open in spreadsheet app
open output/yourname/jobs.csv     # Mac
# xdg-open output/yourname/jobs.csv  # Linux
```

---

## Part 2: Daily Usage

### Scrape → Review → Apply

```bash
# Activate venv (every terminal session)
cd job-hunter && source venv/bin/activate

# 1. Scrape job boards (1-3 min)
python3 run_scrape.py --profile yourname

# 2. Open CSV, mark jobs with Y in the Apply column, save

# 3. Dry run first (browser opens, fills forms, does NOT submit)
python3 run_apply.py --profile yourname --dry-run

# 4. Live run (pauses before each submit for your confirmation)
python3 run_apply.py --profile yourname
```

### Admin panel (optional web UI)

```bash
python3 admin/server.py
# Open http://localhost:5175
```

Dashboard lets you review jobs, run scrapes, manage resumes — all from the browser instead of editing CSVs.

### Automate with cron (optional)

```bash
crontab -e
# Scrape every 12 hours at 8am and 8pm:
0 8,20 * * * cd /path/to/job-hunter && /path/to/venv/bin/python3 run_scrape.py --profile yourname >> output/yourname/cron.log 2>&1
```

### Run tests

```bash
python3 run_tests.py              # All tests (~6 seconds)
python3 run_tests.py --api        # API scraper tests only
python3 run_tests.py --browser    # Playwright tests only
```

---

## Part 3: Hosted Deployment (Server)

Deploy Job Hunter on a server so multiple users can access the admin panel remotely. The CLI tools and auto-apply still run on the server.

### Option A: Linux VPS (DigitalOcean, Linode, AWS EC2, etc.)

**This is the recommended deployment path.** Job Hunter is a Python app with filesystem storage — any Linux server works.

#### 1. Provision a server

- Ubuntu 22.04+ recommended
- Minimum: 1 CPU, 1GB RAM, 10GB disk
- Open port 443 (HTTPS) and 22 (SSH)

#### 2. Install system dependencies

```bash
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx
```

#### 3. Clone and set up

```bash
cd /opt
sudo git clone https://github.com/YOUR_USERNAME/job-hunter.git
sudo chown -R $USER:$USER /opt/job-hunter
cd /opt/job-hunter

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
playwright install chromium
playwright install-deps    # Install system libs for headless Chromium
```

#### 4. Create profiles

```bash
cp profiles/example_profile.py profiles/user1.py
# Edit profiles for each user
# Add resumes to output/user1/resumes/
```

#### 5. Create environment file

```bash
cp .env.example .env
# Edit .env — set ACTIVE_PROFILE, add API keys
```

#### 6. Test locally on the server

```bash
python3 admin/server.py --deployed
# Should print "Open http://localhost:5175"
# Ctrl+C to stop
```

#### 7. Create systemd service

```bash
sudo tee /etc/systemd/system/job-hunter.service > /dev/null << 'EOF'
[Unit]
Description=Job Hunter Admin Panel
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/opt/job-hunter
Environment=DEPLOYED=1
ExecStart=/opt/job-hunter/venv/bin/gunicorn \
    --bind 127.0.0.1:5175 \
    --workers 2 \
    --timeout 120 \
    admin.server:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable job-hunter
sudo systemctl start job-hunter
sudo systemctl status job-hunter    # Verify it's running
```

#### 8. Configure Nginx reverse proxy

```bash
sudo tee /etc/nginx/sites-available/job-hunter > /dev/null << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5175;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        client_max_body_size 10M;
    }
}
EOF
```

```bash
sudo ln -s /etc/nginx/sites-available/job-hunter /etc/nginx/sites-enabled/
sudo nginx -t                    # Test config
sudo systemctl restart nginx
```

#### 9. Add HTTPS (strongly recommended)

```bash
sudo certbot --nginx -d your-domain.com
# Follow prompts — certbot auto-renews
```

#### 10. Add authentication (REQUIRED for public servers)

The admin panel has **no built-in authentication**. You MUST add auth before exposing it to the internet. Two options:

**Option A: Nginx basic auth (simplest)**

```bash
sudo apt install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
# Enter password when prompted
```

Add to the Nginx `location /` block:
```nginx
    auth_basic "Job Hunter";
    auth_basic_user_file /etc/nginx/.htpasswd;
```

```bash
sudo systemctl restart nginx
```

**Option B: Cloudflare Access / Tailscale (zero-trust)**

If using Cloudflare, set up a Cloudflare Access application to gate the domain. If using Tailscale, only expose the server to your tailnet — no public port needed.

#### 11. Set up cron for automated scraping

```bash
crontab -e
```

```cron
# Scrape all profiles every 12 hours
0 8,20 * * * cd /opt/job-hunter && /opt/job-hunter/venv/bin/python3 run_scrape.py --profile user1 >> /opt/job-hunter/output/user1/cron.log 2>&1
0 8,20 * * * cd /opt/job-hunter && /opt/job-hunter/venv/bin/python3 run_scrape.py --profile user2 >> /opt/job-hunter/output/user2/cron.log 2>&1
```

#### 12. Verify deployment

```bash
# Check service is running
sudo systemctl status job-hunter

# Check Nginx is proxying
curl -I https://your-domain.com

# Check admin panel responds
curl -s https://your-domain.com/api/mode
# Should return: {"deployed": true}

# Check profiles load
curl -s https://your-domain.com/api/profiles
```

---

### Option B: Docker

For containerized deployment.

#### Dockerfile

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    wget gnupg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
RUN pip install playwright && playwright install chromium && playwright install-deps

COPY . .

ENV DEPLOYED=1
EXPOSE 5175

CMD ["gunicorn", "--bind", "0.0.0.0:5175", "--workers", "2", "--timeout", "120", "admin.server:app"]
```

#### docker-compose.yml

```yaml
version: "3.8"
services:
  job-hunter:
    build: .
    ports:
      - "5175:5175"
    volumes:
      - ./profiles:/app/profiles
      - ./output:/app/output
      - ./.env:/app/.env
    environment:
      - DEPLOYED=1
    restart: unless-stopped
```

```bash
docker compose up -d
# Admin panel at http://localhost:5175
```

**Note:** Auto-apply (`run_apply.py`) requires a visible browser and doesn't work in Docker without a display server (Xvfb). Run auto-apply outside Docker or set up Xvfb.

---

### Option C: PythonAnywhere (Free Tier)

For a no-server option. Limited — only the admin panel works (no Playwright/auto-apply).

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload the project via the Files tab or clone from GitHub
3. Create a new Web App → Manual configuration → Python 3.10
4. Set the source code path to `/home/yourusername/job-hunter`
5. Set the WSGI file to point to the Flask app:

```python
import sys
sys.path.insert(0, '/home/yourusername/job-hunter')
from admin.server import app as application
```

6. Set environment variable `DEPLOYED=1` in the WSGI file
7. Reload the web app

**Limitations:** No Playwright (no browser automation), no cron on free tier, 512MB RAM limit.

---

## Part 4: Server Maintenance

### Update the code

```bash
cd /opt/job-hunter
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart job-hunter
```

### View logs

```bash
# Service logs
sudo journalctl -u job-hunter -f

# Scrape logs
tail -f output/user1/cron.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Add a new user

```bash
cd /opt/job-hunter && source venv/bin/activate

# Via CLI
cp profiles/example_profile.py profiles/newuser.py
# Edit profile, add resumes to output/newuser/resumes/

# Or via admin panel (deployed mode)
# Click "+ Add User" in the dashboard
```

### Backup

```bash
# Back up profiles, output data, and config
tar czf job-hunter-backup-$(date +%Y%m%d).tar.gz \
    profiles/*.py output/ .env credentials/
```

### Monitor disk usage

```bash
du -sh output/*/         # Per-user data size
du -sh output/*/data/    # Intermediate JSON (can be cleaned)
```

---

## Security Checklist for Hosted Deployments

| Item | Status |
|------|--------|
| HTTPS enabled (certbot/Cloudflare) | |
| Authentication added (basic auth/Cloudflare Access/Tailscale) | |
| Server binds to 127.0.0.1 (Nginx proxies) | |
| `.env` file permissions restricted (`chmod 600 .env`) | |
| Profile files not world-readable | |
| Firewall allows only ports 22, 80, 443 | |
| Automatic security updates enabled (`unattended-upgrades`) | |
| Cron logs rotated or monitored | |
| SSH key auth only (password auth disabled) | |

#!/usr/bin/env bash
set -euo pipefail

# Ensure .env
if [ ! -f .env ]; then
  if [ -f env.sample ]; then
    cp env.sample .env
    echo ".env created from env.sample"
  else
    echo "env.sample not found. Create .env manually before continuing."
    exit 1
  fi
fi

# Ensure Django project exists (avoid overlaying when manage.py exists)
if [ ! -f manage.py ]; then
  if compgen -G "*/wsgi.py" > /dev/null; then
    echo "Detected existing Django project structure (wsgi.py found). Skipping bootstrap."
  else
    echo "Bootstrapping minimal Django project 'config'..."
    docker compose run --rm \
      --volume "$(pwd)":/app \
      --workdir /app \
      app django-admin startproject config .
    echo "Rebuilding image to include new project files..."
    docker compose build
  fi
else
  echo "manage.py exists. Skipping bootstrap."
fi

# Apply migrations
echo "Running migrations..."
# Detect Django module (folder containing wsgi.py)
DETECTED_MODULE=""
if compgen -G "*/wsgi.py" > /dev/null; then
  DETECTED_MODULE=$(dirname $(ls -1 */wsgi.py | head -n1))
  echo "Detected Django module: ${DETECTED_MODULE}"
else
  echo "No wsgi.py found; assuming module: config"
  DETECTED_MODULE="config"
fi

export DJANGO_SETTINGS_MODULE="${DETECTED_MODULE}.settings"
export DJANGO_WSGI_MODULE="${DETECTED_MODULE}.wsgi:application"

# Persist to .env so compose uses correct module later
if grep -q '^DJANGO_SETTINGS_MODULE=' .env; then
  sed -i "s#^DJANGO_SETTINGS_MODULE=.*#DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE//#/\#}#" .env
else
  echo "DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE}" >> .env
fi
if grep -q '^DJANGO_WSGI_MODULE=' .env; then
  sed -i "s#^DJANGO_WSGI_MODULE=.*#DJANGO_WSGI_MODULE=${DJANGO_WSGI_MODULE//#/\#}#" .env
else
  echo "DJANGO_WSGI_MODULE=${DJANGO_WSGI_MODULE}" >> .env
fi

echo "Running migrations with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} DJANGO_WSGI_MODULE=${DJANGO_WSGI_MODULE}..."
docker compose run --rm \
  -e DJANGO_SETTINGS_MODULE \
  -e DJANGO_WSGI_MODULE \
  app python manage.py migrate

# Build and start Django + DB
echo "Building images..."
docker compose build
echo "Starting Django stack..."
DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE}" DJANGO_WSGI_MODULE="${DJANGO_WSGI_MODULE}" docker compose up -d

# Ensure ALLOWED_HOSTS includes requested IPs
TARGET_HOSTS="localhost,127.0.0.1,172.18.252.50"
if grep -q '^ALLOWED_HOSTS=' .env; then
  CURRENT=$(grep '^ALLOWED_HOSTS=' .env | cut -d'=' -f2-)
  MERGED=$(printf "%s,%s" "$CURRENT" "$TARGET_HOSTS" | tr ',' '\n' | sed '/^$/d' | awk '!seen[$0]++' | paste -sd, -)
  sed -i "s#^ALLOWED_HOSTS=.*#ALLOWED_HOSTS=${MERGED//#/\#}#" .env
else
  echo "ALLOWED_HOSTS=${TARGET_HOSTS}" >> .env
fi

# Patch settings.py to read ALLOWED_HOSTS from environment (idempotent)
SETTINGS_FILE="${DETECTED_MODULE}/settings.py"
if [ -f "$SETTINGS_FILE" ] && ! grep -q "os\.environ\.get('ALLOWED_HOSTS'" "$SETTINGS_FILE"; then
  echo "Patching ${SETTINGS_FILE} to read ALLOWED_HOSTS from env..."
  printf "\nimport os\nALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '*').split(',') if h.strip()]\n" >> "$SETTINGS_FILE"
fi

# Patch settings.py to use Postgres if POSTGRES_* present (idempotent)
if [ -f "$SETTINGS_FILE" ] && ! grep -q "django\.db\.backends\.postgresql" "$SETTINGS_FILE"; then
  echo "Patching ${SETTINGS_FILE} to use Postgres when POSTGRES_* env variables are present..."
  cat >> "$SETTINGS_FILE" << 'PY_EOF'

import os
if os.environ.get('POSTGRES_DB') and os.environ.get('POSTGRES_USER') and os.environ.get('POSTGRES_PASSWORD'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'appdb'),
            'USER': os.environ.get('POSTGRES_USER', 'appuser'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'apppass'),
            'HOST': os.environ.get('POSTGRES_HOST', 'db'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        }
    }
PY_EOF
fi

# Install or start SafeLine WAF
echo "Ensuring SafeLine WAF is running..."
if ! docker ps -a --format '{{.Names}}' | grep -q '^safeline-mgt$'; then
  echo "SafeLine not found. Installing via official setup script..."
  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to install SafeLine. Please install curl and re-run."
    exit 1
  fi
  if [ "${EUID}" -ne 0 ]; then
    echo "Elevating privileges with sudo for SafeLine installer..."
    sudo bash -c "$(curl -fsSLk https://waf.chaitin.com/release/latest/setup.sh)"
  else
    bash -c "$(curl -fsSLk https://waf.chaitin.com/release/latest/setup.sh)"
  fi
else
  echo "SafeLine containers found. Starting them..."
  for c in safeline-pg safeline-mgt safeline-detector safeline-tengine safeline-luigi safeline-fvm safeline-chaos; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${c}$"; then
      docker start "${c}" >/dev/null || true
    fi
  done
fi

echo
echo "All set."
echo "- Django:        http://localhost (via WAF when configured) or http://localhost:8000 directly"
echo "- SafeLine UI:   https://localhost:9443 (default from official compose)"
echo "If first-time SafeLine install, get admin creds: docker exec safeline-mgt resetadmin"
echo "Then configure a site in SafeLine with upstream: http://127.0.0.1:8000"
echo "Official SafeLine compose reference: https://waf.chaitin.com/release/latest/compose.yaml"



#!/bin/sh
# apiBase in config.js:
#   - Empty: browser calls same origin (/templates, …); nginx must proxy those paths (docker-compose, some hosts).
#   - Full backend URL (https://…run.app): browser calls the API directly; set via API_BASE env (e.g. Terraform on Cloud Run).
# Do NOT hardcode empty here — that ignored API_BASE from the environment and broke production.
API_BASE="${API_BASE:-}"
AUTH0_DOMAIN="${AUTH0_DOMAIN:-dev-xiwa5ogu3vfhcfba.us.auth0.com}"
AUTH0_CLIENT_ID="${AUTH0_CLIENT_ID:-glHmYjs0pbowPZAtSKaQty4VJjvJnQgO}"

sed -i "s|apiBase: '[^']*'|apiBase: '${API_BASE}'|g" /usr/share/nginx/html/config.js
sed -i "s|auth0Domain: '[^']*'|auth0Domain: '${AUTH0_DOMAIN}'|g" /usr/share/nginx/html/config.js
sed -i "s|auth0ClientId: '[^']*'|auth0ClientId: '${AUTH0_CLIENT_ID}'|g" /usr/share/nginx/html/config.js

# BACKEND_UPSTREAM: host[:port] to proxy API calls to
# BACKEND_SCHEME:   http (docker-compose) or https (Cloud Run)
BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-backend:5000}"
BACKEND_SCHEME="${BACKEND_SCHEME:-http}"
export BACKEND_UPSTREAM BACKEND_SCHEME
envsubst '${BACKEND_UPSTREAM} ${BACKEND_SCHEME}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'

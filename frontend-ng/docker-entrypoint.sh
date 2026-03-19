#!/bin/sh
# Inject API_BASE into config.js at runtime (default: http://localhost:5000)
API_BASE="${API_BASE:-http://localhost:5000}"
sed -i "s|apiBase: '[^']*'|apiBase: '${API_BASE}'|g" /usr/share/nginx/html/config.js

# Generate nginx config from template, substituting BACKEND_UPSTREAM
BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-backend:5000}"
export BACKEND_UPSTREAM
envsubst '${BACKEND_UPSTREAM}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'

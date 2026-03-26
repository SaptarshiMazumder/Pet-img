#!/bin/sh
# Inject runtime config values into config.js
API_BASE="${API_BASE:-http://localhost:5000}"
AUTH0_DOMAIN="${AUTH0_DOMAIN:-dev-xiwa5ogu3vfhcfba.us.auth0.com}"
AUTH0_CLIENT_ID="${AUTH0_CLIENT_ID:-glHmYjs0pbowPZAtSKaQty4VJjvJnQgO}"

sed -i "s|apiBase: '[^']*'|apiBase: '${API_BASE}'|g" /usr/share/nginx/html/config.js
sed -i "s|auth0Domain: '[^']*'|auth0Domain: '${AUTH0_DOMAIN}'|g" /usr/share/nginx/html/config.js
sed -i "s|auth0ClientId: '[^']*'|auth0ClientId: '${AUTH0_CLIENT_ID}'|g" /usr/share/nginx/html/config.js

# Generate nginx config from template, substituting BACKEND_UPSTREAM
BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-backend:5000}"
export BACKEND_UPSTREAM
envsubst '${BACKEND_UPSTREAM}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'

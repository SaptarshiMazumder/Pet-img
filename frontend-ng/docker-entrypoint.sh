#!/bin/sh
# Inject API_BASE into config.js at runtime (default: http://localhost:5000)
API_BASE="${API_BASE:-http://localhost:5000}"
sed -i "s|apiBase: '[^']*'|apiBase: '${API_BASE}'|g" /usr/share/nginx/html/config.js
exec nginx -g 'daemon off;'

# ============================================================
# Pet Generator — Frontend (Angular)
# Multi-stage: Node build → nginx serve
# ============================================================

# Stage 1: Build
FROM node:22-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

RUN apk add --no-cache gettext

COPY --from=build /app/dist/frontend-ng/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN sed -i 's/\r$//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

# Default empty: nginx proxy mode. Override API_BASE at runtime (e.g. Cloud Run → backend URL).
ENV API_BASE=
ENV AUTH0_DOMAIN=dev-xiwa5ogu3vfhcfba.us.auth0.com
ENV AUTH0_CLIENT_ID=glHmYjs0pbowPZAtSKaQty4VJjvJnQgO

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]

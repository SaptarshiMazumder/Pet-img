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

COPY --from=build /app/dist/frontend-ng/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh

RUN sed -i 's/\r$//' /docker-entrypoint.sh && chmod +x /docker-entrypoint.sh

ENV API_BASE=http://localhost:5000

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]

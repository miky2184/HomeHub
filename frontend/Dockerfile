FROM node:22-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Nessun VITE_API_BASE_URL qui di proposito: senza, il frontend chiama /api
# in same-origin (vedi src/api/client.ts) e nginx fa da reverse proxy verso
# il backend (nginx.conf) — funziona identico sia da localhost sul NUC sia
# da IP LAN sia da DDNS, senza dover ricompilare per ogni caso.
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
# .htpasswd viene montato a runtime da docker-compose (non è nell'immagine:
# vedi DEPLOY.md per generarlo)

FROM oven/bun:1 AS build

WORKDIR /app
ARG VITE_CLERK_PUBLISHABLE_KEY
COPY package.json bun.lock ./
RUN bun install --frozen-lockfile
COPY . .
RUN VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY} bun run build

FROM nginx:1.27-alpine AS runtime

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

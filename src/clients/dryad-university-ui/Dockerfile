# Build Stage
FROM node:18-alpine as build

WORKDIR /app

# Install dependencies (legacy-peer-deps to handle React/Cypress versions)
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

# Copy source
COPY . .

# Build for production
RUN npm run build

# Production Stage
FROM nginx:alpine

# Copy custom Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build artifacts
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

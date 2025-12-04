# ===========================
# 1) Build Stage
# ===========================
FROM node:20 AS build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# Build the application (no hardcoded API URL needed)
RUN npm run build

# ===========================
# 2) Serve Stage (nginx)
# ===========================
FROM nginx:stable-alpine

# Copy built files
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

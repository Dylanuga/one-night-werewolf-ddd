FROM node:20-alpine AS build

WORKDIR /app

ARG VITE_SOCKET_URL
ENV VITE_SOCKET_URL=$VITE_SOCKET_URL

ARG VITE_ENABLE_TESTING
ENV VITE_ENABLE_TESTING=$VITE_ENABLE_TESTING

COPY package.json package-lock.json /app/
RUN npm ci

COPY . /app
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

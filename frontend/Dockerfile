FROM node:20-alpine AS build

WORKDIR /app

ARG REACT_APP_BACKEND_URL=""

COPY package.json yarn.lock* ./
RUN yarn install --frozen-lockfile

COPY . .

ENV REACT_APP_BACKEND_URL=${REACT_APP_BACKEND_URL}
RUN yarn build

# Production: serve with nginx
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

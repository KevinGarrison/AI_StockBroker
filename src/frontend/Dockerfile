FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ENV HOST=0.0.0.0
ENV PORT=4000
ENV DANGEROUSLY_DISABLE_HOST_CHECK=true
EXPOSE 4000
CMD ["npm", "start"]

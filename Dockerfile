FROM arm64v8/node:18-buster-slim

RUN npm install -g @11ty/eleventy

RUN mkdir -p /app

WORKDIR /app

COPY . /app/

RUN npm install

RUN npm run build

EXPOSE 8091

CMD [ "npx", "@11ty/eleventy", "--serve", "--port=8091" ]

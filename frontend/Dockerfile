FROM node:20-slim

WORKDIR /app

# npm ci needs the lockfile; copying it separately keeps the install cached
# across source-only changes.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# NEXT_PUBLIC_* values are inlined at build time, so the API URL must be known
# here rather than only at runtime.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]

# ====================
# Stage 1: Dependencies
# ====================
FROM node:20-alpine AS deps

WORKDIR /app

# Copy only package.json (lock file excluded via .dockerignore)
COPY package.json ./

# Install production dependencies - npm will generate fresh lock for Linux platform
RUN npm install --omit=dev && \
    npm cache clean --force

# ====================
# Stage 2: Build
# ====================
FROM node:20-alpine AS builder

WORKDIR /app

# Accept public env vars at build time — Nuxt bakes NUXT_PUBLIC_* into the
# client bundle during `npm run build`, so they must be available here.
ARG NUXT_PUBLIC_API_URL
ARG NUXT_PUBLIC_WS_URL
ENV NUXT_PUBLIC_API_URL=$NUXT_PUBLIC_API_URL
ENV NUXT_PUBLIC_WS_URL=$NUXT_PUBLIC_WS_URL

# Copy only package.json (lock file excluded via .dockerignore)
COPY package.json ./

# Install all dependencies (including dev) - fresh for Linux platform
RUN npm install

# Copy source code
COPY . .

# Ensure proper permissions for development (when builder stage is used directly)
RUN mkdir -p /app/.nuxt /app/node_modules/.cache && \
    chmod -R 777 /app/.nuxt /app/node_modules/.cache

# Set environment variables for build
ENV NODE_ENV=production

# Build the application
RUN npm run build

# ====================
# Stage 3: Production Runtime
# ====================
FROM node:20-alpine AS runner

WORKDIR /app

# Add non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nuxtjs

# Copy dependencies from deps stage
COPY --from=deps --chown=nuxtjs:nodejs /app/node_modules ./node_modules

# Copy built application from builder stage
COPY --from=builder --chown=nuxtjs:nodejs /app/.output ./.output
COPY --from=builder --chown=nuxtjs:nodejs /app/node_modules/.cache ./node_modules/.cache
COPY --from=builder --chown=nuxtjs:nodejs /app/package*.json ./

# Set environment variables
ENV NODE_ENV=production
ENV HOST=0.0.0.0
# PORT can be overridden via docker-compose environment variable

# Switch to non-root user
USER nuxtjs

# Expose port (default 3000, but can be overridden)
EXPOSE 3000

# Health check (uses $PORT environment variable)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-3000}/ || exit 1

# Start the application
CMD ["node", ".output/server/index.mjs"]

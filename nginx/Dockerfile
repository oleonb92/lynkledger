FROM nginx:1.25-alpine

# Remove default nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create SSL directory
RUN mkdir -p /etc/nginx/ssl

# Create static and media directories
RUN mkdir -p /usr/share/nginx/html/static /usr/share/nginx/html/media

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html

# Expose ports
EXPOSE 80 443

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
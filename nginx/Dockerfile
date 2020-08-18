FROM nginx:latest

# Nginx will listen on this port
EXPOSE 80

# Remove the default configuration and copy ours over
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
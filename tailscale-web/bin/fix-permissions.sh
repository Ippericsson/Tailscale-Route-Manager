#!/bin/bash
chown -R www-data:www-data /var/www/Tailscale-Route-Manager/tailscale-web
chmod -R 755 /var/www/Tailscale-Route-Manager/tailscale-web
systemctl restart apache2

# /var/www/Tailscale-Route-Manager/tailscale-web/app.wsgi
import sys
sys.path.insert(0, '/var/www/Tailscale-Route-Manager/tailscale-web')
sys.path.insert(1, '/var/www/Tailscale-Route-Manager/tailscale-web/venv/lib/python3.12/site-packages')  

from tailscaleapp import app as application

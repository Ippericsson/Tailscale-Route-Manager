<img width="1712" height="797" alt="image" src="https://github.com/user-attachments/assets/ff566c09-82d3-4a66-a5f0-8c37997bdbf2" />


# Tailscale-Route-Manager

 **Note**: We are assuming this is a fresh server with only tailscale installed and working<br>
 **Note**: Ensure tailscale is **NOT** running before starting this<br>
 **Note**: This also assumes GitHub SSH has already been setup, if not, you can also download the repo move it to the correct place and unzip it<br>

## 1. Install required packages
sudo apt update <br/>
sudo apt install apache2 libapache2-mod-wsgi-py3 python3-venv python3-pip -y<br/>

## 2. Transfer the tailscale app to server using Git
cd /var/www <br>
git clone git@github.com:IppericssonTailscale-Route-Manager.git<br>

## 4. Create Python virtual environment
cd /var/www/Tailscale-Route-Manager/tailscale-web<br/>
python3 -m venv venv<br/>
source venv/bin/activate<br/>
pip install flask<br/>
deactivate<br/>

## 4.1 Check python version
python3 --version<br/>
vi /var/www/tailscale-web/app.wsgi<br/>
**change version to match your current installed version**


## 5. Apache Config
sudo cp /var/www/Tailscale-Route-Manager/tailscale-web.conf /etc/apache2/sites-available/<br/>
**be sure to update with your actual hostname**<br>
sudo a2ensite tailscale-web.conf<br/>
sudo systemctl reload apache2<br/>

## 6. Fix permissions
mkdir -p /etc/Tailscale-Route-Manager<br>
sudo chown -R www-data:www-data /etc/Tailscale-Route-Manager<br/>
sudo chmod -R 755 /etc/Tailscale-Route-Manager<br/>
sudo chown -R www-data:www-data /var/www/Tailscale-Route-Manager/tailscale-web<br/>
sudo chmod -R 755 /var/www/Tailscale-Route-Manager/tailscale-web<br/>

## 7. Add www-data to sudoers to allow tailscale commands
sudo visudo<br/>

**Add this line at the bottom and save:**
www-data ALL=(ALL) NOPASSWD: /usr/bin/tailscale<br/>

## 8. Set web UI Credentials
cd /var/www/Tailscale-Route-Manager/tailscale-web/bin<br>
chmod +x change_password.sh<br>
./change_password.sh

## === DONE ===
## Visit your app in the browser:
### http://< your-server-ip >/
<br>

# Optional:Replace Logo

Logo file can be found at /var/www/Tailscale-Route-Manager/Tailscale-web/tailscaleapp/static/logo.jpg<br>
replace this with your own logo keeping the same name. <br>

# Optional: Enable HTTPS and redirect 

## 1. Create SSL Directories
mkdir -p /etc/apache2/ssl<br>

## 2. Copy your SSL Files
sudo cp yourdomain.crt /etc/apache2/ssl/<br/>
sudo cp yourdomain.key /etc/apache2/ssl/<br/>
sudo cp yourdomain-ca-bundle.crt /etc/apache2/ssl/  # If applicable<br/>
sudo chmod 600 /etc/apache2/ssl/yourdomain.key<br/>
sudo chown root:root /etc/apache2/ssl/*<br/>

## 3. Enable Apache SSL Module
sudo a2enmod ssl<br/>

## 4. Copy Apache virtual host & disable http
mv /var/www/Tailscale-Route-Manager/tailscale-web-ssl.conf /etc/apache2/sites-available/<br/>
mv /var/www/Tailscale-Route-Manager/tailscale-web-redirect.conf /etc/apache2/sites-available/<br/>
**be sure to update with your actual hostname and update certificate paths**<br>
sudo a2dissite tailscale-web.conf<br/>


## 5. Enable SSL Site and Reload Apache
sudo a2enmod ssl <br>
sudo a2ensite tailscale-web-ssl.conf<br/>
sudo a2ensite tailscale-web-redirect.conf<br/>
sudo systemctl reload apache2<br/>

# How to update
cd /var/www/Tailscale-Route-Manager<br>
git pull<br>
chmod +x ./tailscale-web/bin/fix-permissions.sh<br>
./tailscale-web/bin/fix-permissions.sh <br>






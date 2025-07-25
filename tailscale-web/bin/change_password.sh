#!/bin/bash

# Path to config.py
CONFIG_FILE="/etc/Tailscale-Route-Manager/config.py"

# Prompt for credentials
read -p "Enter new username: " new_user
read -s -p "Enter new password: " new_pass
echo

# Escape inputs for sed or writing
new_user_escaped=$(printf '%s\n' "$new_user" | sed -e 's/[\/&]/\\&/g')
new_pass_escaped=$(printf '%s\n' "$new_pass" | sed -e 's/[\/&]/\\&/g')

# Create config.py if it doesn't exist
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "⚠️ config.py not found, creating..."
    cat <<EOF > "$CONFIG_FILE"
USERNAME = "$new_user_escaped"
PASSWORD = "$new_pass_escaped"
EOF
else
    # Update lines in existing file
    sed -i "s/^USERNAME = .*/USERNAME = \"$new_user_escaped\"/" "$CONFIG_FILE"
    sed -i "s/^PASSWORD = .*/PASSWORD = \"$new_pass_escaped\"/" "$CONFIG_FILE"
fi

# Set file permissions
echo "🔒 Setting config.py permissions..."
chown www-data:www-data "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"

# Restart Apache
echo "🔁 Restarting Apache..."
systemctl restart apache2

# Confirm result
if [[ $? -eq 0 ]]; then
    echo "✅ Credentials updated and Apache restarted successfully."
else
    echo "⚠️ Apache restart failed. Please check logs with: journalctl -u apache2 -xe"
fi

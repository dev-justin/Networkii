#!/usr/bin/env bash

# Exit on any error
set -e

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the current user (the one who sudo'ed)
ACTUAL_USER=$(who am i | awk '{print $1}')
INSTALL_DIR="/home/$ACTUAL_USER/Networkii"

# Create systemd service file
cat > /etc/systemd/system/networkii.service << EOL
[Unit]
Description=Networkii Network Monitor
After=network.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$INSTALL_DIR
Environment=PYTHONPATH=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python3.11 main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

# Set correct permissions
chmod 644 /etc/systemd/system/networkii.service

# Reload systemd daemon
systemctl daemon-reload

# Enable and start service
systemctl enable networkii.service
systemctl start networkii.service

echo "Networkii service has been installed and started!"
echo "You can check its status with: systemctl status networkii"
echo "View logs with: journalctl -u networkii -f" 
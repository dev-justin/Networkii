#!/usr/bin/env bash
#
# install_usb0_setup.sh
# Installs a script (ics.sh) to configure the 'usb0' interface 
# and sets up a systemd service to run it on boot.

set -e

# --- Variables you can customize ---
INTERFACE="usb0"
CON_NAME="usb0"
STATIC_IP="192.168.137.10/24"
GATEWAY="192.168.137.1"
DNS="1.1.1.1"
SETUP_SCRIPT_PATH="/usr/local/bin/ics.sh"
SERVICE_FILE_PATH="/etc/systemd/system/ics.service"

# Define colors and formatting
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Helper function for section headers
print_header() {
    echo -e "\n${BLUE}${BOLD}=== $1 ===${NC}\n"
}

# Helper function for success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Helper function for info messages
print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# 1. Create the NetworkManager config script
print_header "Creating $SETUP_SCRIPT_PATH ..."
sudo tee "$SETUP_SCRIPT_PATH" >/dev/null << EOF
#!/usr/bin/env bash
#
# ics.sh
# Configures the usb0 interface with static IP and gateway for Windows ICS.
# Once this script is run, NetworkManager should remember the settings persistently.

set -e

INTERFACE="$INTERFACE"
CON_NAME="$CON_NAME"
STATIC_IP="$STATIC_IP"
GATEWAY="$GATEWAY"
DNS="$DNS"

# Check if nmcli is present
if ! command -v nmcli >/dev/null 2>&1; then
  echo "Error: nmcli not found. Make sure NetworkManager is installed."
  exit 1
fi

echo "Configuring \$INTERFACE with static IP \$STATIC_IP ..."

# If there is no existing connection for \$CON_NAME, create one
if ! nmcli connection show "\$CON_NAME" >/dev/null 2>&1; then
  echo "No existing connection named '\$CON_NAME' found. Creating new one..."
  sudo nmcli connection add type ethernet ifname "\$INTERFACE" con-name "\$CON_NAME"
fi

# Set static IPv4 configuration
sudo nmcli connection modify "\$CON_NAME" \
  ipv4.method manual \
  ipv4.addresses "\$STATIC_IP" \
  ipv4.gateway "\$GATEWAY" \
  ipv4.dns "\$DNS" \
  ipv6.method ignore \
  connection.autoconnect yes

# Bring up the connection
sudo nmcli connection up "\$CON_NAME"

echo "Done! \$INTERFACE is set to \$STATIC_IP with gateway \$GATEWAY."
EOF

# Make the script executable
print_info "Making $SETUP_SCRIPT_PATH executable..."
sudo chmod +x "$SETUP_SCRIPT_PATH"

# 2. Create the systemd service
print_info "Creating $SERVICE_FILE_PATH ..."
sudo tee "$SERVICE_FILE_PATH" >/dev/null << EOF
[Unit]
Description=Configure usb0 interface on boot
After=network.target

[Service]
Type=oneshot
ExecStart=$SETUP_SCRIPT_PATH
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

print_success "All done! The service has been installed."

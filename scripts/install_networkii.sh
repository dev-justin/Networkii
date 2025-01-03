#!/usr/bin/env bash
#
# Script Name: setup_pi_zero_otg.sh
# Description: Automates enabling USB OTG (RNDIS) on Raspberry Pi Zero,
#              then clones and sets up the Networkii repository.
#
# Usage:       sudo ./setup_pi_zero_otg.sh
#

# Exit immediately if a command exits with a non-zero status.
set -e

# Define boot path
BOOT_PATH="/boot/firmware"

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

#------------------------------
# 1. ENABLE OTG (RNDIS GADGET)
#------------------------------
print_header "Enabling USB OTG (RNDIS)"

# Backup original config files if they haven't been backed up yet.
# We'll only back them up once for safety.
if [ ! -f ${BOOT_PATH}/config.txt.bak ]; then
    print_info "Backing up ${BOOT_PATH}/config.txt to ${BOOT_PATH}/config.txt.bak"
    sudo cp ${BOOT_PATH}/config.txt ${BOOT_PATH}/config.txt.bak
fi

if [ ! -f ${BOOT_PATH}/cmdline.txt.bak ]; then
    print_info "Backing up ${BOOT_PATH}/cmdline.txt to ${BOOT_PATH}/cmdline.txt.bak"
    sudo cp ${BOOT_PATH}/cmdline.txt ${BOOT_PATH}/cmdline.txt.bak
fi

# Enable dwc2 overlay in /boot/firmware/config.txt
# 1) Check if there's an [all] block at all
if grep -q '^\[all\]' "${BOOT_PATH}/config.txt"; then
    # 2) Extract lines from [all] up to the next bracketed section (or EOF)...
    #    Then check if "dtoverlay=dwc2" is already somewhere in there.
    if sed -n '/^\[all\]/, /^\[.*\]/p' "${BOOT_PATH}/config.txt" | grep -q '^dtoverlay=dwc2'; then
        print_info "'dtoverlay=dwc2' is already present under [all]."
    else
        # Insert the line right after [all]
        sudo sed -i '/^\[all\]/a dtoverlay=dwc2' "${BOOT_PATH}/config.txt"
        print_success "Added 'dtoverlay=dwc2' under [all]."
    fi
else
    # 3) If no [all] section exists, create it
    echo -e "\n[all]\ndtoverlay=dwc2" | sudo tee -a "${BOOT_PATH}/config.txt"
    print_success "Added [all] section with 'dtoverlay=dwc2'."
fi

# Add dwc2,g_ether modules load to /boot/firmware/cmdline.txt
# We'll insert them right after 'rootwait'
if ! grep -q "modules-load=dwc2,g_ether" ${BOOT_PATH}/cmdline.txt; then
    print_info "Adding 'modules-load=dwc2,g_ether' to ${BOOT_PATH}/cmdline.txt"
    # Replace the first occurrence of 'rootwait' with 'rootwait modules-load=dwc2,g_ether'
    sudo sed -i 's|\(rootwait\)|\1 modules-load=dwc2,g_ether|' ${BOOT_PATH}/cmdline.txt
    print_success "Successfully added modules to cmdline.txt"
else
    print_info "'modules-load=dwc2,g_ether' already present in ${BOOT_PATH}/cmdline.txt"
fi

print_success "USB OTG (RNDIS) is now enabled. A reboot is recommended to apply changes."


#------------------------------
# 2. UPDATE hostname
#------------------------------
print_header "Updating hostname"

NEW_HOSTNAME="networkii"

# Update hostname using hostnamectl
print_info "Setting hostname to '$NEW_HOSTNAME'"
sudo hostnamectl set-hostname $NEW_HOSTNAME

# Update /etc/hosts
print_info "Updating /etc/hosts"
# Backup hosts file
if [ ! -f /etc/hosts.bak ]; then
    sudo cp /etc/hosts /etc/hosts.bak
    print_info "Backed up /etc/hosts to /etc/hosts.bak"
fi

# Replace old hostname with new one in /etc/hosts
sudo sed -i "s/127.0.1.1.*/127.0.1.1\t$NEW_HOSTNAME/g" /etc/hosts

print_success "Hostname updated to '$NEW_HOSTNAME' in both hostname and /etc/hosts"


#------------------------------
# 3. UPDATE SYSTEM
#------------------------------
print_header "Updating System Packages"

print_info "Updating package lists..."
sudo apt-get update
print_success "Package lists updated"

print_info "Upgrading existing packages..."
sudo apt-get upgrade -y
print_success "System packages upgraded"

#------------------------------
# 4. INSTALL AND SETUP APP REQUIREMENTS    
#------------------------------
print_header "Installing Python Requirements"

# Install required system packages
print_info "Installing required packages..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip python3-dev zlib1g-dev libjpeg-dev libpng-dev libfreetype6-dev libtiff5-dev libopenblas0 network-manager libnss3-tools

# Create config directory
print_info "Setting up configuration directory..."
mkdir -p ~/.config/networkii

# Enable SPI interface for DisplayHATMini
print_info "Enabling SPI interface..."
sudo raspi-config nonint do_spi 0
print_success "SPI interface enabled"

# Create a temporary venv for pipx installation
print_info "Setting up pipx..."
mkdir -p ~/.local/pipx
python3 -m venv ~/.local/pipx/venv
~/.local/pipx/venv/bin/pip install pipx

# Add pipx to PATH for current user
print_info "Adding pipx to PATH..."
PATHLINE='export PATH="$PATH:$HOME/.local/bin"'
if ! grep -q "$PATHLINE" ~/.bashrc; then
    echo "$PATHLINE" >> ~/.bashrc
fi
if [ -f ~/.zshrc ] && ! grep -q "$PATHLINE" ~/.zshrc; then
    echo "$PATHLINE" >> ~/.zshrc
fi

# Update PATH in current session
eval "$PATHLINE"

# Install networkii using pipx
print_info "Installing networkii..."
~/.local/pipx/venv/bin/pipx install --force .
print_success "Networkii installed successfully"

# Ensure PATH is updated in current shell
print_info "Updating current shell PATH..."
export PATH="$PATH:$HOME/.local/bin"
hash -r

print_header "Setup Complete!"
print_success "All installation steps completed successfully"
print_info "You may need to reboot for the OTG (RNDIS) changes to take effect."
print_info "To complete setup, run: ${BOLD}sudo reboot${NC}"
print_info "To use networkii in this session, run: ${BOLD}source ~/.bashrc${NC} (or start a new terminal)"
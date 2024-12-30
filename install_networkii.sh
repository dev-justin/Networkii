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
print_info "To complete setup, run: ${BOLD}sudo reboot${NC}"

#------------------------------
# 2. UPDATE SYSTEM
#------------------------------
print_header "Updating System Packages"

print_info "Updating package lists..."
sudo apt-get update
print_success "Package lists updated"

print_info "Upgrading existing packages..."
sudo apt-get upgrade -y
print_success "System packages upgraded"

#------------------------------
# 3. INSTALL AND SETUP APP REQUIREMENTS    
#------------------------------
print_header "Installing Python Requirements"
pushd "$PROJECT_DIR" > /dev/null

# Install python3-dev
print_info "Installing python3-dev..."
sudo apt-get install -y python3-dev
print_success "python3-dev installed"

# Install dependencies needed for PIL and NumPy
print_info "Installing dependencies needed for PIL and NumPy..."
sudo apt-get install -y zlib1g-dev libjpeg-dev libpng-dev libfreetype6-dev libtiff5-dev libopenblas0
print_success "Dependencies installed"

# Enable SPI interface so we can use DisplayHATMini
print_info "Enabling SPI interface..."
sudo raspi-config nonint do_spi 0
print_success "SPI interface enabled"

# Create virtual environment
print_info "Creating virtual environment..."
python3 -m venv venv
print_success "Virtual environment created"

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Now install dependencies from requirements.txt
if [ -f requirements.txt ]; then
    print_info "Installing pip dependencies in virtual environment..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    print_success "Dependencies installed successfully in virtual environment"
else
    print_info "No requirements.txt found in '$PROJECT_DIR'. Skipping pip install."
fi

popd > /dev/null

print_header "Setup Complete!"
print_success "All installation steps completed successfully"
print_info "You may need to reboot for the OTG (RNDIS) changes to take effect."
print_info "To complete setup, run: ${BOLD}sudo reboot${NC}"
print_info "To use the virtual environment later, run: ${BOLD}source ${PROJECT_DIR}/venv/bin/activate${NC}"
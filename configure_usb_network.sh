#!/usr/bin/env bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configure usb0 interface
echo -e "${YELLOW}Configuring usb0 interface...${NC}"
sudo ip link set usb0 up
sudo ip addr add 192.168.7.2/24 dev usb0
sudo ip route add default via 192.168.7.1

# Test connection
echo -e "${YELLOW}Testing connection...${NC}"
if ping -c 1 8.8.8.8 &> /dev/null; then
    echo -e "${GREEN}✓ Internet connection successful!${NC}"
else
    echo -e "${YELLOW}Note: Internet sharing needs to be enabled on your host computer${NC}"
fi 
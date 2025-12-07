#!/data/data/com.termux/files/usr/bin/bash
# Complete Android App Manager Installer for Termux

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "   ▗▄▄▄       ▗▄▄▄▖    ▗▄▄▄▖ ▗▄▄▄▖▗▄▄▄▖"
echo "  ▐█▄▄▟▖     ▐█▄▄▟▖   ▐█▄▄▟▖▐█▄▄▟▖▐█▄▄▟▖"
echo "  ▐█  ▐█     ▐█  ▐█   ▐█   ▝▐█  ▐█▐█  ▐█"
echo "  ▐█▄▄▟▖     ▐█▄▄▟▖   ▐█▗▄▄▖▐█▄▄▟▖▐█▄▄▟▖"
echo "  ▐█▀▀▜▖     ▐█▀▀▜▖   ▐█▝▀▚▖▐█▀▀▜▖▐█▀▀▜▖"
echo "  ▐█  ▐█     ▐█  ▐█   ▐█   ▝▐█  ▐█▐█  ▐█"
echo "   ▝▀▀▀       ▝▀▀▀    ▝▀▀▀▘ ▝▀▀▀ ▝▀▀▀ "
echo -e "${NC}"
echo -e "${CYAN}Android App Manager - Complete Edition${NC}"
echo -e "${YELLOW}Full-featured app management for Termux${NC}"
echo ""

# Check Termux
if [ ! -d "/data/data/com.termux/files/usr" ]; then
    echo -e "${RED}❌ This script must be run in Termux${NC}"
    echo "Install Termux from F-Droid, then run this script"
    exit 1
fi

echo -e "${BLUE}[1/5] Updating Termux...${NC}"
pkg update -y && pkg upgrade -y

echo -e "${BLUE}[2/5] Installing dependencies...${NC}"
pkg install -y python git

echo -e "${BLUE}[3/5] Installing Python packages...${NC}"
pip install --upgrade pip
pip install rich

echo -e "${BLUE}[4/5] Downloading Android App Manager...${NC}"
# Download the main script
curl -L -o $PREFIX/bin/appmanager https://raw.githubusercontent.com/woo-254/android-app-manager/main/appmanager.py
chmod +x $PREFIX/bin/appmanager

# Create alias
echo "alias aam='appmanager'" >> $HOME/.bashrc

echo -e "${BLUE}[5/5] Setting up Termux...${NC}"
# Create config directory
mkdir -p $HOME/.config/appmanager

echo ""
echo -e "${GREEN}✅ INSTALLATION COMPLETE!${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌟 Quick Start:${NC}"
echo ""
echo -e "${YELLOW}1. First, grant storage permission:${NC}"
echo -e "   ${GREEN}termux-setup-storage${NC}"
echo ""
echo -e "${YELLOW}2. Launch interactive mode:${NC}"
echo -e "   ${GREEN}appmanager${NC}"
echo -e "   ${GREEN}aam${NC} (short alias)"
echo ""
echo -e "${YELLOW}3. Or use command line:${NC}"
echo -e "   ${GREEN}appmanager list${NC}"
echo -e "   ${GREEN}appmanager disable com.bloatware${NC}"
echo -e "   ${GREEN}appmanager uninstall com.unwanted${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${RED}⚠️  CRITICAL WARNING:${NC}"
echo "Never disable:"
echo "  ${RED}com.android.systemui${NC} - Will black screen!"
echo "  ${RED}com.android.phone${NC} - Calls won't work"
echo "  ${RED}com.android.settings${NC} - Can't open settings"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "Run: ${CYAN}appmanager --help${NC}"
echo ""
echo -e "${GREEN}🎉 Enjoy managing your Android apps!${NC}"
echo ""
echo -e "${YELLOW}⭐ Star the repo if you like it!${NC}"
echo "https://github.com/woo-254/android-app-manager"

#!/data/data/com.termux/files/usr/bin/bash
# Android App Manager Installer
# GitHub: https://github.com/woo-254/android-app-manager

echo ""
echo "┌─────────────────────────────────────────┐"
echo "│    📱 Android App Manager Installer     │"
echo "└─────────────────────────────────────────┘"
echo ""

# Check if running in Termux
if [ ! -d "/data/data/com.termux/files/usr" ]; then
    echo "❌ Error: This script must be run in Termux"
    echo "   Install Termux from F-Droid first"
    exit 1
fi

echo "📦 Step 1: Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "🐍 Step 2: Installing Python..."
pkg install -y python

echo "⬇️  Step 3: Downloading Android App Manager..."
# Download the main script
curl -sL "https://raw.githubusercontent.com/woo-254/android-app-manager/main/appmanager.py" -o $PREFIX/bin/appmanager

# Make it executable
chmod +x $PREFIX/bin/appmanager

echo "🔗 Step 4: Creating shortcuts..."
# Create alias
echo "alias aam='appmanager'" >> $HOME/.bashrc

# Also create aam command
ln -sf $PREFIX/bin/appmanager $PREFIX/bin/aam 2>/dev/null || true

echo ""
echo "✅ INSTALLATION COMPLETE!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 HOW TO USE:"
echo ""
echo "1️⃣  First, grant storage permission:"
echo "    termux-setup-storage"
echo ""
echo "2️⃣  Launch interactive mode:"
echo "    appmanager"
echo "    aam   (short alias)"
echo ""
echo "3️⃣  Or use command line:"
echo "    appmanager list"
echo "    appmanager disable com.example.app"
echo "    appmanager enable com.example.app"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  IMPORTANT WARNINGS:"
echo ""
echo "• NEVER disable: com.android.systemui"
echo "• NEVER disable: com.android.phone"
echo "• NEVER disable: com.android.settings"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Need help? Run: appmanager --help"
echo ""
echo "⭐ GitHub: https://github.com/woo-254/android-app-manager"
echo ""

# Reload shell
source $HOME/.bashrc 2>/dev/null || true

echo "🎉 Done! You can now run 'appmanager'"

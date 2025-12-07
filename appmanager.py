#!/data/data/com.termux/files/usr/bin/env python3
"""
Android App Manager - Complete Working Version
GitHub: https://github.com/woo-254/android-app-manager
"""
import os
import sys
import subprocess
import time

# Simple print function
def prt(text):
    print(text)

def run_cmd(cmd):
    """Run a shell command"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), 1

def is_rooted():
    """Check if device is rooted"""
    stdout, stderr, code = run_cmd("su -c 'echo ROOT_TEST'")
    return code == 0 and "ROOT_TEST" in stdout

def get_all_packages():
    """Get all installed packages"""
    packages = []
    
    # Try pm command
    stdout, stderr, code = run_cmd("pm list packages")
    if code == 0 and stdout:
        for line in stdout.strip().split('\n'):
            if line.startswith('package:'):
                packages.append(line[8:].strip())
    
    return sorted(packages)

def get_app_status(package):
    """Check if app is enabled or disabled"""
    stdout, stderr, code = run_cmd(f"pm list packages -d {package}")
    if code == 0 and package in stdout:
        return "disabled"
    return "enabled"

def disable_app(package, rooted):
    """Disable an app"""
    if rooted:
        stdout, stderr, code = run_cmd(f"su -c 'pm disable {package}'")
    else:
        stdout, stderr, code = run_cmd(f"pm disable-user --user 0 {package}")
    
    return code == 0

def enable_app(package):
    """Enable an app"""
    stdout, stderr, code = run_cmd(f"pm enable {package}")
    return code == 0

def uninstall_app(package, rooted, is_system=False):
    """Uninstall an app"""
    if is_system and not rooted:
        return False  # Can't uninstall system apps without root
    
    if rooted:
        stdout, stderr, code = run_cmd(f"su -c 'pm uninstall {package}'")
    else:
        stdout, stderr, code = run_cmd(f"pm uninstall --user 0 {package}")
    
    return code == 0

def clear_app_data(package):
    """Clear app data"""
    stdout, stderr, code = run_cmd(f"pm clear {package}")
    return code == 0 and "Success" in stdout

def is_system_app(package):
    """Check if app is a system app"""
    stdout, stderr, code = run_cmd(f"pm path {package}")
    if code == 0 and stdout:
        if "/system/" in stdout or "/vendor/" in stdout or "/product/" in stdout:
            return True
    return False

def show_header():
    """Show application header"""
    prt("\n" + "="*60)
    prt("          📱 ANDROID APP MANAGER")
    prt("="*60)

def show_main_menu():
    """Show main menu"""
    prt("\n" + "="*60)
    prt("[1] List all apps")
    prt("[2] List system apps")
    prt("[3] List user apps")
    prt("[4] Search packages")
    prt("[5] Manage specific package")
    prt("[6] Refresh list")
    prt("[0] Exit")
    prt("="*60)

def list_apps(packages, app_type="all"):
    """List apps with type filter"""
    count = 0
    for i, package in enumerate(packages, 1):
        is_system = is_system_app(package)
        
        if app_type == "system" and not is_system:
            continue
        if app_type == "user" and is_system:
            continue
        
        status = get_app_status(package)
        status_icon = "✅" if status == "enabled" else "⛔"
        type_icon = "🔴" if is_system else "🟢"
        
        prt(f"{i:4}. {type_icon} {status_icon} {package}")
        count += 1
        
        if count % 15 == 0:
            input("\nPress Enter for more... ")
    
    return count

def manage_package(package, rooted):
    """Manage a specific package"""
    is_system = is_system_app(package)
    status = get_app_status(package)
    
    prt(f"\n📦 Package: {package}")
    prt(f"   Type: {'🔴 System App' if is_system else '🟢 User App'}")
    prt(f"   Status: {'✅ Enabled' if status == 'enabled' else '⛔ Disabled'}")
    prt(f"   Root: {'⚡ Available' if rooted else '⚠️  Not available'}")
    
    # Critical apps warning
    critical_apps = ["com.android.systemui", "com.android.phone", "com.android.settings"]
    if package in critical_apps:
        prt("\n   ⚠️  WARNING: CRITICAL SYSTEM APP!")
        prt("   Do not disable or uninstall!")
    
    prt("\n" + "-"*40)
    prt("[1] Disable" if status == "enabled" else "[1] Enable")
    prt("[2] Uninstall")
    prt("[3] Clear data")
    prt("[4] Show info")
    prt("[0] Back")
    prt("-"*40)
    
    choice = input("\nChoose action: ").strip()
    
    if choice == "1":
        if status == "enabled":
            if package in critical_apps:
                prt("❌ Cannot disable critical system app!")
                return
            confirm = input(f"Disable {package}? (y/n): ").lower()
            if confirm == 'y':
                if disable_app(package, rooted):
                    prt(f"✅ Disabled {package}")
                else:
                    prt(f"❌ Failed to disable {package}")
        else:
            confirm = input(f"Enable {package}? (y/n): ").lower()
            if confirm == 'y':
                if enable_app(package):
                    prt(f"✅ Enabled {package}")
                else:
                    prt(f"❌ Failed to enable {package}")
    
    elif choice == "2":
        if package in critical_apps:
            prt("❌ Cannot uninstall critical system app!")
            return
        
        if is_system and not rooted:
            prt("❌ Cannot uninstall system apps without root!")
            return
        
        confirm = input(f"Uninstall {package}? (y/n): ").lower()
        if confirm == 'y':
            if uninstall_app(package, rooted, is_system):
                prt(f"✅ Uninstalled {package}")
            else:
                prt(f"❌ Failed to uninstall {package}")
    
    elif choice == "3":
        confirm = input(f"Clear ALL data for {package}? (y/n): ").lower()
        if confirm == 'y':
            if clear_app_data(package):
                prt(f"✅ Cleared data for {package}")
            else:
                prt(f"❌ Failed to clear data for {package}")
    
    elif choice == "4":
        prt(f"\n📊 Package Info:")
        prt(f"   Name: {package}")
        prt(f"   Type: {'System' if is_system else 'User'}")
        prt(f"   Status: {'Enabled' if status == 'enabled' else 'Disabled'}")
        
        # Get path
        stdout, stderr, code = run_cmd(f"pm path {package}")
        if code == 0:
            for line in stdout.strip().split('\n'):
                if line.startswith('package:'):
                    prt(f"   Path: {line[8:]}")
    
    input("\nPress Enter to continue...")

def main():
    """Main function"""
    show_header()
    
    # Check environment
    if not os.path.exists("/data/data/com.termux/files/usr"):
        prt("❌ This tool must be run in Termux!")
        prt("👉 Install Termux from F-Droid")
        return
    
    prt("Checking environment...")
    
    # Check root
    rooted = is_rooted()
    if rooted:
        prt("⚡ Root access: Available")
    else:
        prt("⚠️  Root access: Not available")
    
    # Get packages
    prt("Loading packages...")
    packages = get_all_packages()
    
    if not packages:
        prt("❌ No packages found!")
        prt("👉 First run: termux-setup-storage")
        prt("👉 Then restart the app")
        return
    
    prt(f"✅ Loaded {len(packages)} packages")
    
    # Main loop
    while True:
        show_main_menu()
        
        try:
            choice = input("\nChoose option: ").strip()
            
            if choice == "0":
                prt("\n👋 Goodbye!")
                break
            
            elif choice == "1":
                prt(f"\n📱 ALL APPS ({len(packages)} total):")
                count = list_apps(packages, "all")
                prt(f"\n📊 Total: {count} apps")
            
            elif choice == "2":
                prt("\n🔴 SYSTEM APPS:")
                count = list_apps(packages, "system")
                prt(f"\n📊 Total: {count} system apps")
            
            elif choice == "3":
                prt("\n🟢 USER APPS:")
                count = list_apps(packages, "user")
                prt(f"\n📊 Total: {count} user apps")
            
            elif choice == "4":
                search = input("\nSearch term: ").strip().lower()
                if search:
                    prt(f"\n🔍 SEARCH RESULTS for '{search}':")
                    results = [p for p in packages if search in p.lower()]
                    for i, pkg in enumerate(results, 1):
                        status = get_app_status(pkg)
                        status_icon = "✅" if status == "enabled" else "⛔"
                        prt(f"{i:4}. {status_icon} {pkg}")
                    prt(f"\n📊 Found: {len(results)} apps")
                else:
                    prt("❌ Please enter a search term")
            
            elif choice == "5":
                pkg = input("\nEnter package name: ").strip()
                if pkg:
                    if pkg in packages:
                        manage_package(pkg, rooted)
                    else:
                        prt(f"❌ Package not found: {pkg}")
                else:
                    prt("❌ Please enter a package name")
            
            elif choice == "6":
                prt("\n🔄 Refreshing package list...")
                packages = get_all_packages()
                prt(f"✅ Loaded {len(packages)} packages")
            
            else:
                prt("❌ Invalid choice")
        
        except KeyboardInterrupt:
            prt("\n👋 Goodbye!")
            break
        except Exception as e:
            prt(f"❌ Error: {e}")

if _name_ == "_main_":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Android App Manager - Usage:")
            print("  appmanager              # Interactive mode")
            print("  appmanager list         # List all apps")
            print("  appmanager disable <pkg> # Disable app")
            print("  appmanager enable <pkg>  # Enable app")
            print("  appmanager --help       # Show this help")
        elif sys.argv[1] == "list":
            packages = get_all_packages()
            for pkg in packages:
                print(pkg)
        elif sys.argv[1] == "disable" and len(sys.argv) > 2:
            if disable_app(sys.argv[2], is_rooted()):
                print(f"Disabled {sys.argv[2]}")
            else:
                print(f"Failed to disable {sys.argv[2]}")
        elif sys.argv[1] == "enable" and len(sys.argv) > 2:
            if enable_app(sys.argv[2]):
                print(f"Enabled {sys.argv[2]}")
            else:
                print(f"Failed to enable {sys.argv[2]}")
        else:
            main()
    else:
        main()

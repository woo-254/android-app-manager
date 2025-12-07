
import os
import re
import sys
import subprocess
import json
from datetime import datetime

# Try to import Rich for beautiful UI, fallback to simple if not available
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    # Simple print function
    def rprint(*args, **kwargs):
        print(*args)

console = Console() if RICH_AVAILABLE else None

class AndroidAppManager:
    def _init_(self):
        self.rooted = self.check_root()
        self.apps = []
        self.system_apps = []
        self.user_apps = []
        self.critical_apps = [
            "com.android.systemui",
            "com.android.phone",
            "com.android.settings",
            "com.google.android.gms",
            "android",
            "com.android.providers.telephony"
        ]
    
    def check_root(self):
        """Check if device is rooted"""
        checks = ["su -c 'echo ROOT_TEST'", "which su", "id | grep uid=0"]
        for cmd in checks:
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
                if result.returncode == 0 and ('ROOT_TEST' in result.stdout or 'uid=0' in result.stdout):
                    return True
            except:
                continue
        return False
    
    def run_cmd(self, cmd, root=False, timeout=10):
        """Run command with optional root"""
        try:
            if root and self.rooted:
                cmd = f"su -c '{cmd}'"
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Timeout", 1
        except Exception as e:
            return "", str(e), 1
    
    def get_all_packages(self):
        """Get ALL packages using multiple methods"""
        packages = []
        
        # Method 1: pm command
        stdout, stderr, code = self.run_cmd("pm list packages")
        if code == 0:
            for line in stdout.split('\n'):
                if line.startswith('package:'):
                    pkg = line.replace('package:', '').strip()
                    if pkg and pkg not in packages:
                        packages.append(pkg)
        
        # Method 2: Directory scan
        app_dirs = ['/data/app', '/system/app', '/system/priv-app', '/vendor/app']
        for app_dir in app_dirs:
            if os.path.exists(app_dir):
                try:
                    for item in os.listdir(app_dir):
                        if '-' in item:
                            pkg = item.split('-')[0]
                            if '.' in pkg and pkg not in packages:
                                packages.append(pkg)
                except:
                    pass
        
        return sorted(packages)
    
    def categorize_apps(self, packages):
        """Categorize as system or user apps"""
        system = []
        user = []
        
        for pkg in packages:
            stdout, stderr, code = self.run_cmd(f"pm path {pkg}")
            if code == 0 and stdout:
                if any(path in stdout for path in ['/system/', '/vendor/', '/product/']):
                    system.append(pkg)
                else:
                    user.append(pkg)
            else:
                user.append(pkg)  # Default to user
        
        return system, user
    
    def get_app_info(self, package):
        """Get detailed app info"""
        info = {
            'package': package,
            'name': package,
            'version': 'Unknown',
            'path': 'Unknown',
            'uid': 'Unknown',
            'enabled': True
        }
        
        stdout, stderr, code = self.run_cmd(f"pm dump {package}", timeout=15)
        if code == 0:
            lines = stdout.split('\n')
            for line in lines:
                if 'versionName=' in line:
                    info['version'] = line.split('=')[-1].strip()
                elif 'codePath=' in line:
                    info['path'] = line.split('=')[-1].strip()
                elif 'uid=' in line and 'userId' not in line:
                    info['uid'] = line.split('=')[-1].strip()
                elif 'enabled=' in line:
                    info['enabled'] = 'true' in line.lower()
        
        # Check if disabled
        stdout, stderr, code = self.run_cmd(f"pm list packages -d {package}")
        if code == 0 and package in stdout:
            info['enabled'] = False
        
        info['is_system'] = package in self.system_apps
        
        return info
    
    def display_apps_table(self, page=1, search=None):
        """Display apps in a nice table"""
        apps_list = []
        for app in self.user_apps:
            apps_list.append(('user', app))
        for app in self.system_apps:
            apps_list.append(('system', app))
        
        # Apply search filter
        if search:
            search = search.lower()
            apps_list = [(t, p) for t, p in apps_list if search in p.lower()]
        
        # Pagination
        page_size = 15
        total_pages = (len(apps_list) + page_size - 1) // page_size
        page = max(1, min(page, total_pages))
        start = (page - 1) * page_size
        end = min(start + page_size, len(apps_list))
        
        if RICH_AVAILABLE:
            table = Table(title=f"📱 Installed Apps ({len(apps_list)} total) - Page {page}/{total_pages}")
            table.add_column("#", style="cyan")
            table.add_column("Type", style="magenta")
            table.add_column("Package", style="yellow")
            table.add_column("Status", style="green")
            
            for i in range(start, end):
                app_type, package = apps_list[i]
                info = self.get_app_info(package)
                status = "✅ Enabled" if info['enabled'] else "⛔ Disabled"
                type_str = "🔴 System" if app_type == 'system' else "🟢 User"
                table.add_row(str(i+1), type_str, package, status)
            
            console.print(table)
        else:
            print(f"\n📱 Installed Apps ({len(apps_list)} total) - Page {page}/{total_pages}")
            print("="*60)
            for i in range(start, end):
                app_type, package = apps_list[i]
                info = self.get_app_info(package)
                status = "Enabled" if info['enabled'] else "Disabled"
                type_str = "[System]" if app_type == 'system' else "[User]"
                print(f"{i+1:3}. {type_str:8} {package:30} [{status}]")
        
        return apps_list, page, total_pages
    
    def disable_app(self, package):
        """Disable an app"""
        if package in self.critical_apps:
            print(f"⚠️  CRITICAL APP: {package}")
            if not input("Are you SURE? (yes/no): ").lower().startswith('y'):
                print("❌ Cancelled")
                return False
        
        if self.rooted:
            stdout, stderr, code = self.run_cmd(f"pm disable {package}", root=True)
        else:
            stdout, stderr, code = self.run_cmd(f"pm disable-user --user 0 {package}")
        
        if code == 0:
            print(f"✅ Disabled {package}")
            return True
        else:
            print(f"❌ Failed to disable {package}")
            print(f"Error: {stderr}")
            return False
    
    def enable_app(self, package):
        """Enable a disabled app"""
        stdout, stderr, code = self.run_cmd(f"pm enable {package}")
        
        if code == 0:
            print(f"✅ Enabled {package}")
            return True
        else:
            print(f"❌ Failed to enable {package}")
            return False
    
    def uninstall_app(self, package):
        """Uninstall an app"""
        is_system = package in self.system_apps
        
        if is_system and not self.rooted:
            print("❌ Cannot uninstall system apps without root")
            return False
        
        if package in self.critical_apps:
            print(f"⚠️  CRITICAL SYSTEM APP: {package}")
            print("DO NOT UNINSTALL! Use 'disable' instead")
            return False
        
        if is_system:
            stdout, stderr, code = self.run_cmd(f"pm uninstall -k {package}", root=True)
        else:
            stdout, stderr, code = self.run_cmd(f"pm uninstall --user 0 {package}")
        
        if code == 0:
            print(f"✅ Uninstalled {package}")
            return True
        else:
            print(f"❌ Failed to uninstall {package}")
            print(f"Error: {stderr}")
            return False
    
    def clear_app_data(self, package):
        """Clear app data"""
        stdout, stderr, code = self.run_cmd(f"pm clear {package}")
        
        if code == 0 and 'Success' in stdout:
            print(f"✅ Cleared data for {package}")
            return True
        else:
            print(f"❌ Failed to clear data for {package}")
            return False
    
    def backup_app(self, package, output_dir="."):
        """Backup APK file"""
        stdout, stderr, code = self.run_cmd(f"pm path {package}")
        if code == 0:
            for line in stdout.split('\n'):
                if line.startswith('package:'):
                    apk_path = line.replace('package:', '').strip()
                    filename = f"{package}.apk"
                    output_path = os.path.join(output_dir, filename)
                    
                    if self.rooted:
                        self.run_cmd(f"cp {apk_path} {output_path}", root=True)
                    else:
                        # Try to copy without root
                        try:
                            import shutil
                            shutil.copy(apk_path, output_path)
                        except:
                            print(f"❌ Need root to backup {package}")
                            return False
                    
                    print(f"✅ Backed up to {output_path}")
                    return True
        
        print(f"❌ Could not find APK for {package}")
        return False

def main_menu():
    """Interactive main menu"""
    manager = AndroidAppManager()
    
    if RICH_AVAILABLE:
        console.print(Panel.fit(
            "[bold green]Android App Manager[/bold green]\n"
            "[cyan]Complete app management for Termux[/cyan]",
            border_style="green"
        ))
    else:
        print("\n" + "="*50)
        print("       ANDROID APP MANAGER")
        print("="*50)
    
    print(f"📦 Loading packages...")
    manager.apps = manager.get_all_packages()
    
    if not manager.apps:
        print("❌ No packages found!")
        print("👉 Run: termux-setup-storage")
        return
    
    manager.system_apps, manager.user_apps = manager.categorize_apps(manager.apps)
    
    print(f"✅ Found {len(manager.apps)} packages")
    print(f"   🟢 User apps: {len(manager.user_apps)}")
    print(f"   🔴 System apps: {len(manager.system_apps)}")
    
    if manager.rooted:
        print("   ⚡ Root: Available (full access)")
    else:
        print("   ⚠️  Root: Not available (some features limited)")
    
    page = 1
    search_term = None
    
    while True:
        apps_list, page, total_pages = manager.display_apps_table(page, search_term)
        
        print("\n" + "="*50)
        print("[1] Manage package    [2] Next page")
        print("[3] Prev page         [4] Search")
        print("[5] Refresh           [6] Backup app")
        print("[7] Batch operations  [0] Exit")
        print("="*50)
        
        try:
            choice = input("\nChoose option: ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            
            elif choice == "1":
                try:
                    num = int(input(f"Package number (1-{len(apps_list)}): "))
                    if 1 <= num <= len(apps_list):
                        app_type, package = apps_list[num-1]
                        is_system = app_type == 'system'
                        
                        info = manager.get_app_info(package)
                        
                        print(f"\n📋 Package: {package}")
                        print(f"   Type: {'🔴 System' if is_system else '🟢 User'}")
                        print(f"   Version: {info['version']}")
                        print(f"   Status: {'✅ Enabled' if info['enabled'] else '⛔ Disabled'}")
                        print(f"   UID: {info['uid']}")
                        
                        if package in manager.critical_apps:
                            print("   ⚠️  WARNING: Critical system app!")
                        
                        print("\n[1] Disable" if info['enabled'] else "\n[1] Enable")
                        print("[2] Uninstall")
                        print("[3] Clear data")
                        print("[4] Backup APK")
                        print("[0] Back")
                        
                        action = input("Action: ").strip()
                        
                        if action == "1":
                            if info['enabled']:
                                if input(f"Disable {package}? (y/n): ").lower() == 'y':
                                    manager.disable_app(package)
                            else:
                                if input(f"Enable {package}? (y/n): ").lower() == 'y':
                                    manager.enable_app(package)
                        
                        elif action == "2":
                            if input(f"Uninstall {package}? (y/n): ").lower() == 'y':
                                manager.uninstall_app(package)
                        
                        elif action == "3":
                            if input(f"Clear ALL data for {package}? (y/n): ").lower() == 'y':
                                manager.clear_app_data(package)
                        
                        elif action == "4":
                            output_dir = input("Output directory [./]: ").strip() or "."
                            manager.backup_app(package, output_dir)
                    
                    else:
                        print("❌ Invalid number")
                except ValueError:
                    print("❌ Enter a valid number")
            
            elif choice == "2":
                if page < total_pages:
                    page += 1
                else:
                    print("📄 Already on last page")
            
            elif choice == "3":
                if page > 1:
                    page -= 1
                else:
                    print("📄 Already on first page")
            
            elif choice == "4":
                search = input("Search term: ").strip()
                if search:
                    search_term = search
                    page = 1
                else:
                    search_term = None
            
            elif choice == "5":
                print("🔄 Refreshing...")
                manager.apps = manager.get_all_packages()
                manager.system_apps, manager.user_apps = manager.categorize_apps(manager.apps)
                page = 1
                search_term = None
            
            elif choice == "6":
                pkg = input("Package to backup: ").strip()
                if pkg:
                    output_dir = input("Output directory [./]: ").strip() or "."
                    manager.backup_app(pkg, output_dir)
            
            elif choice == "7":
                print("\n📦 Batch Operations:")
                print("[1] Disable all user apps (except selected)")
                print("[2] Enable all disabled apps")
                print("[0] Back")
                
                batch_choice = input("Choose: ").strip()
                
                if batch_choice == "1":
                    keep = input("Packages to keep (comma separated): ").strip().split(',')
                    keep = [p.strip() for p in keep if p.strip()]
                    
                    count = 0
                    for package in manager.user_apps:
                        if package not in keep and package not in manager.critical_apps:
                            if manager.disable_app(package):
                                count += 1
                    
                    print(f"✅ Disabled {count} apps")
                
                elif batch_choice == "2":
                    count = 0
                    for package in manager.apps:
                        info = manager.get_app_info(package)
                        if not info['enabled']:
                            if manager.enable_app(package):
                                count += 1
                    
                    print(f"✅ Enabled {count} apps")
        
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if _name_ == "_main_":
    # Check if running in Termux
    if not os.path.exists("/data/data/com.termux/files/usr"):
        print("⚠️  This tool is designed for Termux on Android")
        print("   Install Termux from F-Droid first")
        sys.exit(1)
    
    # Check for CLI arguments
    if len(sys.argv) > 1:
        manager = AndroidAppManager()
        
        if sys.argv[1] == "list":
            manager.apps = manager.get_all_packages()
            manager.system_apps, manager.user_apps = manager.categorize_apps(manager.apps)
            
            for app in manager.user_apps:
                print(f"🟢 {app}")
            for app in manager.system_apps:
                print(f"🔴 {app}")
        
        elif sys.argv[1] == "disable" and len(sys.argv) > 2:
            manager.disable_app(sys.argv[2])
        
        elif sys.argv[1] == "enable" and len(sys.argv) > 2:
            manager.enable_app(sys.argv[2])
        
        elif sys.argv[1] == "uninstall" and len(sys.argv) > 2:
            manager.uninstall_app(sys.argv[2])
        
        elif sys.argv[1] == "root-check":
            print("✅ Rooted" if manager.rooted else "❌ Not rooted")
        
        else:
            print("Usage:")
            print("  appmanager                    # Interactive mode")
            print("  appmanager list              # List all apps")
            print("  appmanager disable <pkg>     # Disable app")
            print("  appmanager enable <pkg>      # Enable app")
            print("  appmanager uninstall <pkg>   # Uninstall app")
            print("  appmanager root-check        # Check root status")
    else:
        main_menu()
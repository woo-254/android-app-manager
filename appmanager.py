import os
import time
import subprocess
import sys
from rich import print
from rich.progress import track
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm

console = Console()

def check_pydroid_environment():
    """Check if running in Pydroid 3 and setup proper environment"""
    console.print("[cyan]Detecting environment...[/cyan]")
    
    # Check if we're in Pydroid 3
    try:
        # Pydroid 3 specific paths
        termux_prefix = "/data/data/com.termux"
        pydroid_prefix = "/data/data/ru.iiec.pydroid3"
        
        if os.path.exists(pydroid_prefix):
            console.print("[green]✓ Running in Pydroid 3[/green]")
            return "pydroid"
        elif os.path.exists(termux_prefix):
            console.print("[green]✓ Running in Termux[/green]")
            return "termux"
        else:
            console.print("[yellow]⚠ Unknown Android environment[/yellow]")
            return "unknown"
    except:
        return "unknown"

def execute_command(command, timeout=10):
    """Execute shell command with proper environment for Pydroid 3"""
    try:
        # For Pydroid 3, we need to use the QPython method or alternative
        env = os.environ.copy()
        
        # Try to use QPython's androidhelper if available
        try:
            from androidhelper import Android
            droid = Android()
            if "pm list packages" in command:
                result = droid.getLaunchableApplications()
                if result:
                    packages = []
                    for app in result.result:
                        if isinstance(app, dict) and 'package' in app:
                            packages.append(f"package:{app['package']}")
                        elif isinstance(app, str):
                            packages.append(f"package:{app}")
                    return "\n".join(packages), "", 0
        except ImportError:
            pass
        
        # Try alternative method using app_process
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env
        )
        return result.stdout, result.stderr, result.returncode
        
    except subprocess.TimeoutExpired:
        return "", "Timeout expired", 1
    except Exception as e:
        return "", str(e), 1

def list_packages_pydroid():
    """Get packages list specifically for Pydroid 3"""
    packages = []
    
    console.print("[cyan]Fetching installed packages...[/cyan]")
    
    # Method 1: Try using Android's package manager via app_process
    console.print("[yellow]Trying method 1: Using app_process...[/yellow]")
    stdout, stderr, code = execute_command(
        'CLASSPATH=/system/framework/pm.jar app_process /system/bin com.android.commands.pm.Pm list packages'
    )
    
    if code == 0 and stdout:
        for line in stdout.split('\n'):
            if line.startswith('package:'):
                packages.append(line.replace('package:', '').strip())
        console.print(f"[green]✓ Found {len(packages)} packages via app_process[/green]")
        return packages
    
    # Method 2: Try using settings command
    console.print("[yellow]Trying method 2: Using settings...[/yellow]")
    stdout, stderr, code = execute_command('settings list system')
    
    if code == 0:
        # Parse system settings for installed packages
        for line in stdout.split('\n'):
            if 'installed' in line.lower() and 'package' in line.lower():
                parts = line.split('=')
                if len(parts) > 1:
                    pkg = parts[0].strip()
                    if pkg and '.' in pkg:  # Likely a package name
                        packages.append(pkg)
    
    # Method 3: Check app directories (requires root)
    console.print("[yellow]Trying method 3: Scanning app directories...[/yellow]")
    app_dirs = [
        '/data/app',           # User apps
        '/system/app',         # System apps
        '/system/priv-app',    # Privileged system apps
        '/product/app',        # Product apps
        '/vendor/app',         # Vendor apps
    ]
    
    for app_dir in app_dirs:
        if os.path.exists(app_dir):
            try:
                for item in os.listdir(app_dir):
                    if item.endswith('.apk') or '-' in item:
                        # Extract package name from directory name
                        # Format is usually: com.example.app-1
                        if '-' in item:
                            pkg = item.split('-')[0]
                            if pkg not in packages:
                                packages.append(pkg)
            except:
                pass
    
    # Method 4: Try to use Android Debug Bridge (ADB) if available
    console.print("[yellow]Trying method 4: Checking ADB...[/yellow]")
    stdout, stderr, code = execute_command('which adb')
    if code == 0 and 'adb' in stdout:
        stdout, stderr, code = execute_command('adb shell pm list packages')
        if code == 0:
            for line in stdout.split('\n'):
                if line.startswith('package:'):
                    packages.append(line.replace('package:', '').strip())
    
    # Remove duplicates and sort
    packages = sorted(list(set(packages)))
    console.print(f"[green]✓ Total found: {len(packages)} packages[/green]")
    
    return packages

def list_packages():
    """Main function to list packages"""
    env = check_pydroid_environment()
    
    if env == "pydroid":
        return list_packages_pydroid()
    else:
        # Try standard method
        try:
            console.print("[cyan]Using standard pm command...[/cyan]")
            result = subprocess.run(
                ['pm', 'list', 'packages'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = []
                for line in result.stdout.split('\n'):
                    if line.startswith('package:'):
                        packages.append(line.replace('package:', '').strip())
                console.print(f"[green]✓ Found {len(packages)} packages[/green]")
                return packages
            else:
                console.print("[yellow]Standard method failed, trying Pydroid method...[/yellow]")
                return list_packages_pydroid()
                
        except Exception as e:
            console.print(f"[yellow]Standard method error: {e}[/yellow]")
            return list_packages_pydroid()

def categorize_packages(packages: list) -> tuple:
    """Categorize packages into system and user apps"""
    system_apps = []
    user_apps = []
    
    if not packages:
        return system_apps, user_apps
    
    console.print("[cyan]Categorizing apps...[/cyan]")
    
    for pkg in track(packages, description="Processing..."):
        try:
            # Method 1: Check app directory
            system_paths = [
                f'/system/app/{pkg}',
                f'/system/priv-app/{pkg}',
                f'/system/app/{pkg}-1',
                f'/system/priv-app/{pkg}-1',
                f'/product/app/{pkg}',
                f'/product/app/{pkg}-1',
                f'/vendor/app/{pkg}',
                f'/vendor/app/{pkg}-1',
            ]
            
            is_system = False
            for path in system_paths:
                if os.path.exists(path):
                    is_system = True
                    break
            
            if is_system:
                system_apps.append(pkg)
            else:
                # Check data directory
                user_path = f'/data/data/{pkg}'
                if os.path.exists(user_path):
                    user_apps.append(pkg)
                else:
                    # Default to user app if unsure
                    user_apps.append(pkg)
                    
        except Exception as e:
            console.print(f"[yellow]Warning: Could not categorize {pkg}[/yellow]")
            user_apps.append(pkg)
    
    return system_apps, user_apps

def disable_app(pkg: str) -> bool:
    """Disable an app - limited functionality in Pydroid"""
    console.print(f"[yellow]Attempting to disable {pkg}...[/yellow]")
    
    # In Pydroid, we have limited capabilities
    console.print("[red]⚠ Warning: Pydroid 3 has limited permissions[/red]")
    console.print("[yellow]You may need to use ADB or a rooted device for this action[/yellow]")
    
    # Try using app_process method
    stdout, stderr, code = execute_command(
        f'CLASSPATH=/system/framework/pm.jar app_process /system/bin com.android.commands.pm.Pm disable {pkg}'
    )
    
    if code == 0:
        console.print(f"[green]✓ Disable command sent for {pkg}[/green]")
        console.print("[yellow]Note: Check if app is actually disabled[/yellow]")
        return True
    else:
        console.print(f"[red]✗ Cannot disable {pkg} from Pydroid[/red]")
        console.print("[cyan]Alternative methods:[/cyan]")
        console.print("1. Use ADB from computer: adb shell pm disable-user --user 0 PACKAGE_NAME")
        console.print("2. Use a rooted file manager app")
        console.print("3. Use Android Settings → Apps")
        return False

def uninstall_app(pkg: str) -> bool:
    """Uninstall an app - limited functionality in Pydroid"""
    console.print(f"[yellow]Attempting to uninstall {pkg}...[/yellow]")
    
    console.print("[red]⚠ Warning: Pydroid 3 cannot directly uninstall apps[/red]")
    console.print("[cyan]Use one of these methods instead:[/cyan]")
    console.print("1. [bold]ADB (from computer):[/bold]")
    console.print("   adb shell pm uninstall --user 0 " + pkg)
    console.print("\n2. [bold]Android Settings:[/bold]")
    console.print("   Settings → Apps → [App Name] → Uninstall")
    console.print("\n3. [bold]Root required methods:[/bold]")
    console.print("   - Use Root Explorer to delete APK files")
    console.print("   - Use Titanium Backup or similar apps")
    
    # We can still try to send an intent to uninstall
    try:
        from androidhelper import Android
        droid = Android()
        # Try to launch uninstall intent
        droid.startActivity('android.intent.action.DELETE', f'package:{pkg}')
        console.print("[green]✓ Launched uninstall dialog[/green]")
        return True
    except:
        console.print("[yellow]Could not launch uninstall dialog[/yellow]")
        return False

def show_apps_table(user_apps: list, system_apps: list) -> tuple:
    """Display apps in a table"""
    table = Table(title="Installed Apps", show_lines=True)
    table.add_column("No.", style="cyan", justify="right", width=5)
    table.add_column("Type", style="magenta", width=12)
    table.add_column("Package Name", style="yellow")
    
    all_apps = []
    idx = 1
    
    # User apps
    for app in user_apps:
        table.add_row(str(idx), "[green]User[/green]", app)
        all_apps.append(("user", app))
        idx += 1
    
    # System apps
    for app in system_apps:
        table.add_row(str(idx), "[red]System[/red]", app)
        all_apps.append(("system", app))
        idx += 1
    
    console.print(table)
    console.print(f"[cyan]Total: {len(all_apps)} apps ({len(user_apps)} user, {len(system_apps)} system)[/cyan]")
    
    return all_apps

def main():
    console.print("[bold green]Android App Manager for Pydroid 3[/bold green]")
    console.print("[yellow]Note: Pydroid has limited permissions[/yellow]")
    console.print("[cyan]Some features may require ADB or root access[/cyan]")
    
    # Get packages
    packages = list_packages()
    
    if not packages:
        console.print("[red]No packages found![/red]")
        console.print("\n[cyan]Troubleshooting:[/cyan]")
        console.print("1. Grant storage permission to Pydroid 3")
        console.print("2. Try using ADB from a computer")
        console.print("3. Root your device for full access")
        console.print("4. Use Termux instead for better compatibility")
        return
    
    # Categorize
    system_apps, user_apps = categorize_packages(packages)
    
    # Show table
    all_apps = show_apps_table(user_apps, system_apps)
    
    # Warning
    console.print("\n[bold red]⚠️  IMPORTANT WARNINGS:[/bold red]")
    console.print("1. Do NOT uninstall critical system apps")
    console.print("2. Pydroid 3 has limited permissions")
    console.print("3. Some actions may require ADB or root")
    console.print("4. Backup important data before proceeding")
    
    risky_apps = [
        "com.android.phone",
        "com.android.systemui",
        "com.android.settings",
        "android",
        "com.google.android.gms"
    ]
    
    while True:
        console.print("\n" + "="*50)
        console.print("[cyan]Options:[/cyan]")
        console.print("1. View package details")
        console.print("2. Get ADB command for package")
        console.print("3. Attempt to disable package")
        console.print("4. Refresh list")
        console.print("0. Exit")
        
        choice = Prompt.ask("Select", choices=["0", "1", "2", "3", "4"])
        
        if choice == "0":
            break
            
        elif choice == "4":
            console.print("[cyan]Refreshing...[/cyan]")
            packages = list_packages()
            system_apps, user_apps = categorize_packages(packages)
            all_apps = show_apps_table(user_apps, system_apps)
            
        elif choice in ["1", "2", "3"]:
            # Show package list
            console.print("\n[cyan]Packages:[/cyan]")
            for i, (app_type, pkg) in enumerate(all_apps, 1):
                type_icon = "🟢" if app_type == "user" else "🔴"
                console.print(f"{i:3}. {type_icon} {pkg}")
            
            try:
                choice_idx = IntPrompt.ask(
                    f"\nEnter package number (1-{len(all_apps)})",
                    default=1,
                    show_default=True
                )
                
                if 1 <= choice_idx <= len(all_apps):
                    app_type, pkg = all_apps[choice_idx - 1]
                    
                    if choice == "1":  # View details
                        console.print(f"\n[cyan]Package: {pkg}[/cyan]")
                        console.print(f"Type: {'User' if app_type == 'user' else 'System'}")
                        console.print(f"Risky: {'YES ⚠️' if pkg in risky_apps else 'No'}")
                        
                        # Try to get more info
                        stdout, stderr, code = execute_command(
                            f'CLASSPATH=/system/framework/pm.jar app_process /system/bin com.android.commands.pm.Pm path {pkg}'
                        )
                        if code == 0 and stdout:
                            console.print(f"Path: {stdout.strip()}")
                        
                    elif choice == "2":  # ADB commands
                        console.print(f"\n[green]ADB Commands for {pkg}:[/green]")
                        console.print(f"Disable: [yellow]adb shell pm disable-user --user 0 {pkg}[/yellow]")
                        console.print(f"Enable:  [yellow]adb shell pm enable {pkg}[/yellow]")
                        console.print(f"Uninstall: [yellow]adb shell pm uninstall --user 0 {pkg}[/yellow]")
                        console.print(f"\n[cyan]To use ADB:[/cyan]")
                        console.print("1. Enable USB debugging in Developer Options")
                        console.print("2. Connect device to computer via USB")
                        console.print("3. Run commands in terminal/command prompt")
                        
                    elif choice == "3":  # Disable
                        if pkg in risky_apps:
                            console.print(f"[bold red]⚠️  WARNING: {pkg} is CRITICAL![/bold red]")
                            if not Confirm.ask("[yellow]Continue anyway?[/yellow]"):
                                continue
                        
                        if Confirm.ask(f"Attempt to disable {pkg}?"):
                            disable_app(pkg)
                            
            except ValueError:
                console.print("[red]Invalid input[/red]")
            except KeyboardInterrupt:
                continue
    
    console.print("[bold cyan]Goodbye![/bold cyan]")

if _name_ == "_main_":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Interrupted[/bold cyan]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")

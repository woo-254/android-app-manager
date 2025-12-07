# 📱 Android App Manager for Termux

[![Termux](https://img.shields.io/badge/Termux-Compatible-brightgreen)](https://termux.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> *The most complete Android app management tool for Termux - No root required!*

Manage ALL your Android apps directly from Termux terminal. Disable bloatware, uninstall apps, clear data, backup APKs, and more!

## ✨ Features

### 🔍 App Discovery
- List ALL installed apps (system & user)
- Smart categorization (system vs user)
- Search by package name
- Paginated display

### ⚙️ Management
- *Disable/Enable apps* (no root required!)
- *Uninstall apps* (user apps without root, all with root)
- *Clear app data* (free up storage)
- *Backup APK files* (save apps before uninstall)
- *Batch operations* (disable multiple apps at once)

### 🛡️ Safety
- Critical app protection (prevents system breakage)
- Root detection & appropriate methods
- Confirmation prompts for dangerous actions
- Backup warnings

### 🎨 Interface
- Beautiful terminal UI (with Rich)
- Both interactive & command-line modes
- Color-coded output
- Progress indicators

## 🚀 One-Command Installation

Open *Termux* and run:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR-USERNAME/android-app-manager/main/install.sh | bash
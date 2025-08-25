# CyberLAB Flask App – Auto-Start Setup

This guide explains how to run the CyberLAB Flask app automatically on **Windows** and **Linux**, with consistent behavior across both systems.

---
## 📦 Requirements

### Python Version
- Python **3.8+** (recommended 3.10 or higher)

### Required Packages
Install dependencies inside your virtual environment:

```bash
pip install flask requests

```

## 🚀 Windows Setup

### 1. Create Shortcut
1. Press **Win + R**, type `shell:startup`, and hit Enter.  
2. Inside the Startup folder, create a new shortcut:  
   - **Target**:
     ```
     <path-to-project>\venv\Scripts\pythonw.exe "<path-to-project>\app.py"
     ```
   - **Start in**:
     ```
     <path-to-project>
     ```

   ✅ Use `pythonw.exe` instead of `python.exe` to hide the console window.

### 2. Environment
- Ensure `AiqToken` is set as a **System Environment Variable**, or hardcode it in your code.
- Relative paths (e.g., `config.json`) work if *Start in* points to your project folder.

### 3. Behavior
- The app runs automatically when the user logs in.
- The console window is hidden.
- Flask app behaves the same as when started manually.

---

## 🐧 Linux Setup (systemd)

### 1. Create Service File

Create `/etc/systemd/system/cyberlab.service`:

```ini
[Unit]
Description=CyberLAB Flask App
After=network.target

[Service]
User=<username>
WorkingDirectory=<path-to-project>
ExecStart=<path-to-project>/venv/bin/python app.py
Environment="AIQ_TOKEN=<your-api-token>"
Environment="PATH=<path-to-project>/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

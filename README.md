# CyberLAB Flask App – Setup Guide

This guide explains how to run the CyberLAB Flask App automatically on **Windows** and **Linux**.  
The app is distributed as a ready-to-run executable — **no Python installation is required**.

---

## 📦 Requirements

- Install the **AttackIQ Agent** on the machine.  
- Set the **API token** as a system environment variable.

### Set Environment Variable (one-liner)

Run this command in PowerShell **as Administrator** (replace `YOUR_TOKEN_HERE`):

```powershell
setx AiqToken "YOUR_TOKEN_HERE" /M

# 📱 Scrcpy Live Control Center & ADB Streamer (Universal Hero Edition)

[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Scrcpy](https://img.shields.io/badge/Powered%20By-Scrcpy%20v3+-orange.svg)](https://github.com/Genymobile/scrcpy)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An advanced **Direct3D11 hardware-accelerated Control Center and Process Supervisor** for Android screen mirroring, device automation, and bidirectional streaming via [Scrcpy](https://github.com/Genymobile/scrcpy) and Android Debug Bridge (ADB).

The live mobile phone display is the **central hero** of the interface, with power management, input virtualization, recording pipelines, camera streaming, and wireless networking seamlessly integrated into a single cohesive desktop workstation.

---

## ✨ Key Capabilities

### 1. 📱 Embedded Live Hero Display
* **Direct3D11 Pipeline**: Ultra low-latency rendering directly embedded into the Control Center layout.
* **Layout Management**: Switch dynamically between **In-App Embedded**, **Docked Side-by-Side**, or **Floating Pop-Out** window.
* **Full Mouse & Keyboard Pass-through**: Click, swipe, scroll, and type into Android apps directly from your PC.

### 2. ⚡ Physical Screen Power & Battery Saver
* **⚡ Screen OFF Mode**: Turns off the physical phone screen entirely (saving battery and stopping device overheating) while the PC mirror stays **100% active, visible, and fully interactive**.
* **💡 Screen ON**: Instantly powers the physical mobile display back on.
* **🔓 Wake & Unlock**: Dual-pipeline wake command that turns on the display and dismisses the swipe lockscreen without touching the phone.

### 3. 🖱️ Xiaomi / POCO / HyperOS Hardware UHID Support
* Bypasses standard MIUI / HyperOS USB touch restrictions using kernel-level USB HID emulation (`--keyboard=uhid --mouse=uhid`).
* Full mouse clicking, smooth vertical scroll wheel, and typing work out of the box with zero specialized vendor settings required.

### 4. 🎮 Instant Live Mode Shifter
Switch between operational modes on the fly without spawning separate command terminals:
* 🎮 **Full Interactive Control**: Hardware UHID active, mouse & keyboard control.
* 🔋 **Screen-Off Battery Saver**: Physical phone screen OFF, mirror fully active on PC.
* 👁️ **View-Only Monitor**: Inputs disabled, ideal for live presentations and walkthroughs.
* 📷 **Mobile Webcam**: High-resolution 30 FPS webcam feed with front/rear sensor switching.
* 🤖 **PC-to-Phone Streamer**: Streams PC desktop screen to Android for **Google Assistant / Gemini Live** voice-to-voice screen reading.
* 🔴 **Record MP4**: Direct hardware-accelerated video recording saved to `recordings/`.
* 🔊 **Audio-Only Stream**: Route phone audio to PC speakers with video encoding paused.

### 5. 📶 1-Click Smart Wi-Fi Connection
* Automatically detects the device's wireless LAN IP address via ADB.
* Configures ADB over TCP/IP (port 5555) and establishes a wireless link.
* Safely unplug your USB cable and maintain full wireless control.

### 6. 🎨 Eye-Care Themes & Dynamic UI Zoom
* **☀️ Day & 🌙 Midnight Dark Modes**: High-contrast, eye-friendly palettes.
* **🔍 Dynamic Font Scaling**: Zoom UI controls up or down using `Ctrl + Mouse Wheel` or `A-` / `A+` buttons.

---

## 📂 Repository Structure

```
Scrcpy-Live-Control-Center/
├── control_center.py          # Primary PyQt6 Control Center GUI & Process Supervisor
├── pc_to_phone_streamer.py    # Bidirectional PC-to-Android screen streaming server
├── setup_scrcpy.ps1           # 1-Click automatic downloader for Scrcpy & ADB
├── Start_Control_Center.bat   # Windows 1-Click launcher
├── Start_Control_Center.vbs   # Silent / background launcher (no console flash)
├── requirements.txt           # Python dependencies (PyQt6)
├── presets/                   # Standalone 1-click batch presets:
│   ├── 1_Full_Interactive_Control.bat
│   ├── 2_Screen_Off_Battery_Saver.bat
│   ├── 3_View_Only_Monitor.bat
│   ├── 4_OTG_Hardware_Mouse_Keyboard.bat
│   ├── 5_Webcam_Stream.bat
│   ├── 6_Audio_Only.bat
│   ├── 7_Virtual_Secondary_Display.bat
│   ├── 8_Wireless_Connect.bat
│   ├── 9_Record_Screen_MP4.bat
│   └── 10_Share_PC_Screen_to_Google_Assistant.bat
├── .speckit/                  # Spec-Driven Development architecture docs
│   ├── constitution.md
│   └── specs/001-scrcpy-live-control-center/
├── .gitignore
├── LICENSE                    # MIT License
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
* **Windows 10 / 11**
* **Python 3.10+** installed and added to PATH
* **Android Phone** with **USB Debugging** enabled in Developer Options

### 2. 1-Click Automatic Setup
Run the setup script in PowerShell to automatically install dependencies and download official Scrcpy + ADB binaries:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_scrcpy.ps1
```

> **Manual Alternative**: If you already have `scrcpy` and `adb` installed via `winget install Genymobile.scrcpy` or on your system PATH, the application will detect them automatically!

### 3. Launching the Control Center
Double-click `Start_Control_Center.bat` (or `Start_Control_Center.vbs`), or launch from the terminal:

```powershell
python control_center.py
```

---

## ⌨️ Shortcut Reference

| Action | Shortcut / Input | Description |
| :--- | :--- | :--- |
| **Release Mouse** | `Left-Alt` | Releases cursor from phone mirror back to Windows desktop |
| **Turn Screen OFF** | `Alt + O` | Turns off physical screen; PC mirror stays interactive |
| **Turn Screen ON** | `Alt + Shift + O` | Turns physical screen back on |
| **Android Back** | Right-Click / `Alt + B` | Navigates back (wakes screen if asleep) |
| **Android Home** | Middle-Click / `Alt + H` | Returns to Android home screen |
| **Recent Apps** | `Alt + S` | Opens app switcher / multitasking |
| **Notification Shade** | `Alt + N` | Pulls down top notifications |
| **Volume Up / Down** | `Alt + Up` / `Alt + Down` | Adjusts phone media volume |
| **Wake & Dismiss** | Click `🔓 Wake Screen` | Dual-pipeline wake command via ADB & Scrcpy |

---

## 🤖 PC-to-Phone Streamer (AI Assistant Integration)

The included `pc_to_phone_streamer.py` utility lets you broadcast your PC desktop to your mobile device over a high-speed local MJPEG stream on port `8766`.

### Use Case
Allows mobile AI assistants (such as **Google Assistant with Gemini Live**) running on your phone to inspect your PC monitor, answer questions about code or design files on your screen, and converse with you voice-to-voice in real time.

```powershell
python pc_to_phone_streamer.py
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Underlying screen mirroring engine is powered by [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy) (Apache 2.0).

# 📱 Scrcpy Live Control Center v4.1 (Universal Hero Edition)

Welcome! The Scrcpy suite has been transformed into a **Unified Live Control Center**, where your **live phone screen is the central hero**, with all controls, power toggles, mode shifters, and telemetry seamlessly arranged beside it in a single cohesive window.

---

## 🚀 Quick Launch

- **Double-Click**: [`Start_Control_Center.vbs`](file:///C:/Users/ROC%20STORE/Desktop/scrcpy-win64-v3.3.4/scrcpy-win64-v3.3.4/Start_Control_Center.vbs) (or [`Start_Control_Center.bat`](file:///C:/Users/ROC%20STORE/Desktop/scrcpy-win64-v3.3.4/scrcpy-win64-v3.3.4/Start_Control_Center.bat))
- The Control Center opens with your live mobile screen embedded front and center, ready for direct mouse and keyboard interaction.

---

## 🌟 What's New & Key Highlights

### 1. 📱 The Live Mobile Screen is the Hero
- Your phone display is rendered live inside the Control Center using high-speed Direct3D11.
- Direct click, drag, scroll, and type using your PC mouse and keyboard.
- **🗖 Pop Out / 🗔 Dock Screen**: Detach the live phone screen into an independent floating window anytime, or keep it docked inside the Control Center.

### 2. ⚡ Instant Physical Screen Power Management
- **Screen OFF (Battery Saver)**: Click `⚡ Screen OFF` to turn off your physical mobile phone screen completely to save battery and stop phone overheating, while your PC mirror stays **100% LIVE and fully controllable**!
- **Screen ON**: Click `💡 Screen ON` to turn the physical phone display back on.
- **Wake & Unlock**: Click `🔓 Wake Screen` to wake the device from sleep, turn the display on, and dismiss the swipe lockscreen without touching your phone.

### 3. 🎮 Instant Live Mode Shifting (No Extra Windows!)
Switch modes on the live screen instantly with one click:
- 🎮 **Full Control**: Screen on, Hardware UHID active, mouse & keyboard control.
- 🔋 **Screen-Off Battery Saver**: Physical phone screen OFF, mirror fully interactive on PC.
- 👁️ **View-Only Monitor**: Read-only mirroring (inputs disabled) for presentations.
- 📷 **Mobile Webcam**: High-resolution 30 FPS true colors with front/rear sensor selector.
- 🤖 **PC Screen to Phone**: Streams PC screen to mobile for **Google Assistant / Gemini Live** voice-to-voice text reading.
- 🔴 **Record MP4**: Mirrors and records video directly to the `recordings/` folder.
- 🔊 **Audio-Only Stream**: Listen to phone audio on PC speakers with video paused.

### 4. 🖱️ Xiaomi / POCO Hardware UHID Input Fix
- Standard touch injection on Xiaomi / POCO devices is blocked unless Xiaomi security settings are enabled.
- **Our Solution**: Hardware UHID emulation (`--keyboard=uhid --mouse=uhid`) runs kernel-level USB HID simulation, enabling full mouse clicking, wheel scrolling, and keyboard typing out of the box!
- **Mouse Bindings**:
  - **Left-Click**: Tap / Touch
  - **Right-Click**: Back button (powers on screen if asleep!)
  - **Middle-Click**: Home button
  - **Scroll Wheel**: Smooth vertical scrolling
  - **Left-Alt**: Releases the mouse pointer back to Windows desktop

### 5. 🛡️ Lock Screen Pattern & Black Screen Clarification
- **Why does the screen go black on pattern/PIN?** Android has an internal security shield (`FLAG_SECURE`) that turns the video feed black specifically while drawing patterns or entering PINs to prevent malware from capturing passwords. As soon as you unlock, the screen immediately reappears!
- **💡 Permanent Fix**: Open phone **Settings -> Additional settings -> Developer options** and turn **ON**: `Stay awake (Screen will never sleep while charging)`. Your phone will never lock or go black while connected to your PC!

### 6. 📶 1-Click Smart Wi-Fi Connection
- Click `📶 Connect Wi-Fi`:
  - Automatically identifies your phone's Wi-Fi IP address.
  - Switches to TCP/IP port 5555.
  - Connects wirelessly so you can safely unplug your USB cable!
  - Fully robust error feedback (no empty error pop-ups).

### 7. ☀️ Day & 🌙 Night Modes + Snapping & Zoom
- **☀️ / 🌙 Toggle**: Instant switch between eye-friendly warm midnight dark theme and clean soft daylight theme.
- **📐 Snap Layout**: Snap Left (50%), Snap Right (50%), Compact Side-Dock (460px width), Center Floating (75%), or Maximize.
- **🔍 Font Zoom**: `Ctrl + Mouse Wheel` or `A-` / `A+` buttons to scale the interface text up or down dynamically.

---

## ⌨️ Shortcut Quick Reference

| Action | Shortcut / Click | Description |
| :--- | :--- | :--- |
| **Release Mouse** | `Left-Alt` | Releases mouse cursor from mirror back to Windows desktop |
| **Turn Screen OFF** | `Alt + O` | Turns physical screen off, keeps PC mirror live |
| **Turn Screen ON** | `Alt + Shift + O` | Turns physical screen back on |
| **Back Button** | Right-Click / `Alt + B` | Navigates back (powers screen on if asleep) |
| **Home Button** | Middle-Click / `Alt + H` | Returns to Android home screen |
| **Recent Apps** | `Alt + S` | Opens recent apps / multitasking switcher |
| **Notification Shade**| `Alt + N` | Pulls down top notifications |
| **Volume Up / Down**| `Alt + Up` / `Alt + Down` | Changes phone volume |
| **Wake & Dismiss** | `🔓 Wake Screen` Button | Dual-pipeline wake command via ADB & Scrcpy |

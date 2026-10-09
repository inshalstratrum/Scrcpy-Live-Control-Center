# Feature Specification: Scrcpy Live Control Center

**Feature ID**: 001-scrcpy-live-control-center  
**Status**: In Progress  
**Authors**: Antigravity AI & User  

---

## 1. Executive Summary
Provide a unified, robust, accessible GUI Control Center for Android screen mirroring and management using Scrcpy v4.1 on Windows. The **hero of the application is the live phone screen**, flanked by an intuitive, non-cluttered control rail. The tool provides zero-hassle mode shifting, instant physical screen power toggles (battery saver), Xiaomi UHID input compatibility, and stable Wi-Fi pairing.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Live Hero Screen with Docked / Floating Flexibility
- **Description**: As a user, I want the phone screen to be live immediately upon opening the app, seamlessly docked beside the controls.
- **Acceptance Criteria**:
  1. The live phone screen starts with high-performance Direct3D11 rendering.
  2. The window is positioned either docked magnetically beside the Control Center or embedded directly inside the frame.
  3. A 1-click `🗖 Pop Out / 🗔 Re-Dock` button allows detaching the mirror to an independent floating window or returning it to the docked cockpit.
  4. Closing or moving the Control Center keeps the live screen in sync.

### User Story 2: Physical Screen Power Management (Battery Saver + Wake)
- **Description**: As a user, I want to turn off the physical phone screen to save battery and reduce heat, while maintaining full mouse and keyboard control on my PC.
- **Acceptance Criteria**:
  1. Clicking `⚡ Screen OFF` turns the physical phone display completely dark within 200ms.
  2. The PC mirror continues streaming at full resolution and 60 FPS.
  3. Clicking `💡 Screen ON` turns the physical phone display back on.
  4. Clicking `🔓 Wake Screen` turns on the display from sleep and dismisses the swipe lock screen.

### User Story 3: Seamless Single-Screen Mode Shifting
- **Description**: As a user, I want to switch between operational modes with one click without opening separate terminal windows or restarting Python scripts manually.
- **Acceptance Criteria**:
  1. Modes available:
     - 🎮 Full Interactive Control (UHID Mouse & Keys)
     - 🔋 Screen-Off Battery Saver
     - 👁️ View-Only Monitor (No inputs)
     - 📷 Mobile Webcam (Smooth 30 FPS, True Color, Front/Rear selector)
     - 🤖 PC Screen to Mobile (Reverse streamer for Google Assistant)
     - 🔴 Record MP4 (Direct capture to `recordings/`)
     - 🔊 Audio-Only Stream
  2. Shifting mode terminates any active session, cleans up ADB forward tunnels, and initializes the new mode in < 1.5 seconds.

### User Story 4: Xiaomi / POCO Input Reliability
- **Description**: As a user on a Xiaomi POCO device, I want full mouse clicking, wheel scrolling, and keyboard typing without being blocked by MIUI/HyperOS permission restrictions.
- **Acceptance Criteria**:
  1. Hardware UHID (`--keyboard=uhid --mouse=uhid --mouse-bind=bhsn:++++`) is the default input engine.
  2. Left-click taps/drags, right-click triggers Back (and wakes device if asleep), middle-click triggers Home, wheel scrolls.
  3. Pressing `Left-Alt` releases cursor back to Windows desktop.

### User Story 5: 1-Click Wi-Fi Connection & Wireless Freedom
- **Description**: As a user, I want to connect to my phone over Wi-Fi without confusing errors so I can unplug my USB cable.
- **Acceptance Criteria**:
  1. Detects device's Wi-Fi IP automatically (`192.168.1.4`).
  2. If already connected wirelessly, displays a clear notification and sets the target to Wi-Fi.
  3. If connecting, enables TCP/IP 5555 and connects. Captures both stdout and stderr; NEVER presents an empty dialog.

### User Story 6: Visual Accessibility, Snapping & Themes
- **Description**: As a user, I want comfortable text size, eye-care lighting, and quick monitor window placement.
- **Acceptance Criteria**:
  1. Header includes a `☀️ / 🌙 Day & Night` mode switch.
  2. `Ctrl + Mouse Wheel` and `A-` / `A+` buttons smoothly scale UI text from 11px to 22px.
  3. `📐 Snap Layout` menu snaps to Left 50%, Right 50%, Compact Side Dock (460px), Center (75%), and Maximize.

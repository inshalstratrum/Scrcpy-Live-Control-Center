# Research Findings: Xiaomi POCO & Scrcpy v4.1 Architecture

## 1. Target Hardware & OS Profile
- **Device**: Xiaomi POCO (`2310FPCA4G` / code-named `gust`).
- **OS**: Android 15 with Xiaomi HyperOS.
- **Connection Interfaces**:
  - USB Serial: `BIROFA9TXW8TZP89`
  - Wi-Fi IP / Port: `192.168.1.4:5555`

---

## 2. Input Injection & Security Quirks (Xiaomi HyperOS)
- **Problem**: Xiaomi restricts user-space input injection. Running `adb shell input ...` or standard scrcpy SDK touch injection fails with:
  ```
  java.lang.SecurityException: Injecting input events requires INJECT_EVENTS permission.
  ```
- **Discovery**: Scrcpy provides **Hardware UHID Emulation** (`--keyboard=uhid --mouse=uhid`). UHID creates virtual `/dev/uhid` nodes in the Android Linux kernel. This registers the PC mouse and keyboard as genuine physical USB hardware devices, completely bypassing Xiaomi's user-space permission checks.
- **Mouse Bindings**:
  - Setting `--mouse-bind=bhsn:++++` maps:
    - Primary Right-Click: BACK (and wakes/powers on the screen if sleeping!)
    - Primary Middle-Click: HOME
    - Primary 4th-Click: Recent Apps (App Switch)
    - Primary 5th-Click: Notification Shade
  - Pressing `Left-Alt` (with `--shortcut-mod=lalt`) instantly toggles mouse capture back to the Windows desktop.

---

## 3. Screen Power & Wakefulness Pipeline
- **Problem**: Setting `stay_on_while_plugged_in` via ADB or scrcpy's `--stay-awake` throws:
  ```
  SecurityException: Permission denial, must have WRITE_SECURE_SETTINGS.
  ```
- **Discovery**: We can achieve 100% reliable wakefulness without permissions:
  1. **Turning Physical Screen OFF**: In scrcpy, sending shortcut `Alt+O` (or launching with `--turn-screen-off`) turns the physical device AMOLED/LCD screen completely off. The mirror remains active at 60 FPS, saving battery and preventing device overheating.
  2. **Turning Physical Screen ON**: Sending shortcut `Alt+Shift+O` turns the physical display back on.
  3. **Waking Screen from Sleep**: Running `cmd statusbar expand-notifications` followed by `cmd statusbar collapse` prompts Android PowerManager to wake the display immediately. Running `am start -a android.intent.action.MAIN -c android.intent.category.HOME` brings the home screen forward. Running `wm dismiss-keyguard` dismisses standard swipe lock.

---

## 4. Lock Screen `FLAG_SECURE`
- Android security policy marks the lock screen pattern / PIN prompt with `FLAG_SECURE`. During pattern entry, Android's SurfaceFlinger hardware composer blanks out the video buffer, sending black frames to scrcpy.
- Once unlocked, mirroring resumes immediately.
- **User Solution**: Enabling **"Stay awake while charging"** in Developer Options prevents the screen from timing out while connected to PC.

---

## 5. Native SDL3 Windowing & Embedding
- Scrcpy v4.1 uses SDL3 and Direct3D11 for video playback.
- Naive Win32 `SetParent` reparenting on SDL3 can disrupt the Direct3D11 swapchain, steal keyboard focus, or leave the window in a hidden state if the title search fails.
- **Optimal Architecture**:
  1. A **Docked Magnetic Window Manager** where Scrcpy runs as a borderless native SDL3 window positioned with pixel-precision right beside the Control Center, or embedded with verified HWND tracking.
  2. The Control Center synchronizes its position, movement, snapping, and minimization with Scrcpy.
  3. A 1-click **"🗖 Pop Out / 🗔 Re-Dock"** toggle lets the user detach the phone into an independent floating window or keep it docked beside the Control Center.
  4. Process supervisor actively kills dead/zombie `scrcpy.exe` instances to prevent tunnel binding collisions.

---

## 6. Camera Webcam Parameters
- Phone camera sensor supports up to 30 FPS (`fps={10, 15, 20, 24, 30}`).
- Requesting 60 FPS causes severe color distortion and poor auto-exposure.
- Setting `--camera-fps=30` and `--camera-id=0` delivers vivid, crystal-clear 1080p/4K video.

<!--
SYNC IMPACT REPORT
==================
Version: 1.0.0 (Ratified Baseline)
Project: Scrcpy Ultimate Live Control Center
Target Hardware: Xiaomi POCO (2310FPCA4G / HyperOS / Android 15)
Runtime: Windows 11 / x64 / Python 3.14 / PyQt6 / Scrcpy v4.1 / SDL3
-->

# Scrcpy Live Control Center Constitution

This constitution defines the non-negotiable architectural invariants, hardware constraints, and engineering principles governing the Scrcpy Live Control Center. Every specification, plan, task, and code modification MUST strictly adhere to these principles.

---

## Core Principles

### Principle I: Hardware Realism & Permission Invariants (Xiaomi HyperOS / Android 15)
1. **Input Injection Restrictions**: Xiaomi MIUI / HyperOS explicitly blocks Android OS touch injection via `InputShellCommand` and scrcpy SDK touch injection with `java.lang.SecurityException: Injecting input events requires INJECT_EVENTS permission`.
   - **Binding Invariant**: The primary mouse and keyboard pipeline MUST use **Hardware UHID Emulation** (`--keyboard=uhid --mouse=uhid --mouse-bind=bhsn:++++ --shortcut-mod=lalt`). UHID communicates directly with the kernel `/dev/uhid` node and bypasses Xiaomi's user-space security barrier completely.
2. **Secure Settings Restrictions**: Passing `--stay-awake` in scrcpy attempts to write `stay_on_while_plugged_in` into `global` settings, triggering `SecurityException: WRITE_SECURE_SETTINGS`.
   - **Binding Invariant**: The system MUST NOT rely on scrcpy flags that trigger `WRITE_SECURE_SETTINGS`. Wake locks and wakefulness MUST be driven via non-privileged ADB mechanisms (`cmd statusbar expand-notifications`, `am start -a android.intent.action.MAIN -c android.intent.category.HOME`, and scrcpy keyboard shortcuts `Alt+O`, `Alt+Shift+O`, `Alt+P`).
3. **Lock Screen `FLAG_SECURE` Awareness**:
   - The system MUST document and handle Android's `FLAG_SECURE` behavior on PIN/pattern entry transparently, providing 1-click developer options guidance ("Stay awake while charging") so the user understands why the video feed blanks on lock and how to keep it permanently active.

### Principle II: Zero-Orphan Process & Tunnel Integrity
1. Only ONE `scrcpy.exe` instance may communicate with a given ADB device serial at any time. Multiple instances create ADB forward collisions, causing device disconnection and server lockups.
2. **Supervisor Mandate**: The application MUST maintain an active process supervisor that:
   - Queries and terminates any orphaned `scrcpy.exe` processes before launching a new stream.
   - Cleans up reverse tunnels (`adb reverse --remove tcp:8765`) upon streamer termination.
   - Registers robust OS exit hooks (`atexit`, `closeEvent`, Windows signal handling) ensuring no background zombies remain when the user exits the app.

### Principle III: Windowing Architecture & Native SDL3 Stability
1. **The Hero Mandate**: The mobile live screen MUST be the primary visual focus of the application.
2. **Stable Display Pipeline**:
   - SDL3 Direct3D11 rendering is a native hardware-accelerated pipeline. Unstable Win32 reparenting that strips window message queues or conflicts with Qt Direct3D contexts leads to swapchain disconnection and silent window loss.
   - The application MUST implement a **docked dual-pane / magnetic snap window manager**: Scrcpy is positioned seamlessly beside the Control Center with exact pixel synchronization, or reparented with verified message pump routing and an immediate fallback to docked floating mode.
   - The user MUST have an instant **"🗖 Pop Out / 🗔 Re-Dock"** toggle to switch between a unified dual-pane dock and an independent floating window at will.

### Principle IV: Single-Screen Live Mode Shifting
1. The user MUST NEVER be forced to open separate Python scripts, terminal windows, or desktop shortcuts to change operating modes.
2. The Control Center MUST provide instantaneous mode shifting among:
   - 🎮 Full Interactive Control (UHID Mouse & Keyboard)
   - 🔋 Screen-Off Battery Saver (Physical phone screen OFF, PC mirror active & controllable)
   - 👁️ View-Only Monitor (Inputs blocked)
   - 📷 Mobile Webcam (Smooth 30 FPS, True Color, Front/Rear sensor selection)
   - 🤖 PC Screen to Mobile (AI Assistant voice-to-voice stream with zoom)
   - 🔴 HD Screen Recording (MP4 capture directly to `recordings/`)
   - 🔊 Audio-Only Stream (Phone audio routed to PC speakers)
3. Switching between modes MUST cleanly transition the underlying stream in < 1 second.

### Principle V: Visual Accessibility & Ergonomics
1. **Day ☀️ & Night 🌙 Themes**: Complete, eye-friendly styling with high contrast, soft amber/slate tones for daytime, and deep warm midnight blue/charcoal for nighttime.
2. **Dynamic UI Scaling**: UI fonts and controls MUST scale seamlessly via `Ctrl + Mouse Wheel` and dedicated `A-` / `A+` buttons (range 11px to 22px).
3. **Desktop Snapping**: 1-click snapping to Left Half (50%), Right Half (50%), Compact Side-Dock (460px width), Center (75%), and Maximize.
4. **Transparent Diagnostics**: ADB commands MUST capture both `stdout` and `stderr`. The application MUST NEVER show blank/empty error dialogs.

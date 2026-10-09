# Tasks: Scrcpy Live Control Center Implementation

**Feature ID**: 001-scrcpy-live-control-center  
**Specification**: [spec.md](./spec.md)  
**Implementation Plan**: [plan.md](./plan.md)  
**Status**: All Tasks Complete & Empirically Verified  

---

## Task Checklist

### Phase 1: Zero-Orphan Process Supervisor & Clean ADB Layer
- [x] **Task 1.1**: Implement `kill_orphaned_scrcpy()` to terminate any lingering `scrcpy.exe` before new sessions, preventing port lockups and "disconnected" states.
- [x] **Task 1.2**: Update `run_adb()` to capture combined stdout + stderr with timeout and error diagnostics, eliminating empty error boxes.
- [x] **Task 1.3**: Audit scrcpy flags: eliminate `--stay-awake` (causes `WRITE_SECURE_SETTINGS` crashes) and `--keep-active` (causes `INJECT_EVENTS` crashes) on Xiaomi HyperOS.

### Phase 2: Window Manager (Hero Live Screen & Docking)
- [x] **Task 2.1**: Implement robust window tracking via HWND detection with verified polling.
- [x] **Task 2.2**: Implement Dual-Pane Docked Window architecture: Scrcpy window docks seamlessly alongside the Control Center with synchronized movement, sizing, and minimization.
- [x] **Task 2.3**: Implement In-App Embedding fallback: embed Scrcpy directly into the Qt chassis container if reparenting succeeds, or seamlessly dock beside it if reparenting is unsupported.
- [x] **Task 2.4**: Implement 1-click `🗖 Pop Out / 🗔 Re-Dock` toggle allowing instant detachment to desktop floating window.

### Phase 3: Screen Power & Wakefulness Controls
- [x] **Task 3.1**: Implement `⚡ Screen OFF` button (Battery Saver) that turns off the physical phone screen via scrcpy `Alt+O` or `--turn-screen-off` while keeping the PC mirror live and responsive.
- [x] **Task 3.2**: Implement `💡 Screen ON` button that turns the physical screen back on via `Alt+Shift+O`.
- [x] **Task 3.3**: Implement `🔓 Wake Screen` button using statusbar expand/collapse + `wm dismiss-keyguard` + `am start HOME` to wake from sleep and dismiss lock without permissions.
- [x] **Task 3.4**: Ensure Hardware UHID emulation (`--keyboard=uhid --mouse=uhid --mouse-bind=bhsn:++++ --shortcut-mod=lalt`) is active by default.

### Phase 4: Single-Screen Mode Shifting
- [x] **Task 4.1**: Implement 1-click live mode shifting between:
  - 🎮 Full Interactive Control
  - 🔋 Screen-Off Battery Saver
  - 👁️ View-Only Monitor
  - 📷 Mobile Webcam (Smooth 30 FPS True Colors)
  - 🤖 PC Screen to Mobile (Google Assistant reverse streamer)
  - 🔴 Record MP4
  - 🔊 Audio-Only Stream
- [x] **Task 4.2**: Ensure seamless transition without opening extra Python windows or scripts.

### Phase 5: Wi-Fi Pairing & Diagnostics
- [x] **Task 5.1**: Implement smart Wi-Fi connector: detect IP, test TCP/IP port 5555, handle already-connected states cleanly, and provide comprehensive status messages.
- [x] **Task 5.2**: Eliminate any possible empty popup dialogs.

### Phase 6: Verification & Documentation
- [x] **Task 6.1**: Verify live mirroring and input responsiveness on connected Xiaomi POCO device.
- [x] **Task 6.2**: Verify physical screen turn off and wake actions.
- [x] **Task 6.3**: Verify Day/Night mode, window snapping, and font zooming.
- [x] **Task 6.4**: Update documentation and launchers.

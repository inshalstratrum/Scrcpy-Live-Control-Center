#!/usr/bin/env python3
"""
PC-to-Phone Screen Streamer for Google Assistant / Gemini Live
Shares PC Desktop screen to Android phone in high resolution over ADB / Wi-Fi.
Mobile Google Assistant can read the PC screen clearly and converse voice-to-voice.
"""

import sys
import os

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import time
import socket
import threading
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Ensure we can run in headless/offscreen mode if no GUI display is attached
os.environ["QT_QPA_PLATFORM"] = "windows"

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QBuffer, QIODevice
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

PORT = 8766
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
import shutil

ADB_PATH = os.path.join(SCRIPT_DIR, "adb.exe")
if not os.path.exists(ADB_PATH):
    bin_path = os.path.join(SCRIPT_DIR, "bin", "adb.exe")
    if os.path.exists(bin_path):
        ADB_PATH = bin_path
    else:
        ADB_PATH = shutil.which("adb") or "adb"

# Global stream state
app_instance = None
current_frame = None
frame_lock = threading.Lock()
is_streaming = False
stream_fps = 20
jpeg_quality = 80
scale_factor = 1.0  # 1.0 = native resolution

def get_local_ip():
    """Retrieve local LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def ensure_qapp():
    """Ensure QApplication instance is initialized in the main thread."""
    global app_instance
    if app_instance is None:
        app_instance = QApplication.instance()
        if app_instance is None:
            app_instance = QApplication(sys.argv)
    return app_instance

def screen_capture_loop():
    """Background worker continuously grabbing the primary monitor screen."""
    global current_frame, is_streaming, app_instance
    
    if not PYQT_AVAILABLE:
        print("[!] PyQt6 is required for screen capture.")
        return

    qapp = ensure_qapp()
    screen = qapp.primaryScreen()
    if screen is None:
        print("[!] No primary screen found.")
        return

    print("[*] Screen capture worker active.")
    while is_streaming:
        t_start = time.time()
        try:
            pixmap = screen.grabWindow(0)
            if scale_factor != 1.0:
                new_w = int(pixmap.width() * scale_factor)
                new_h = int(pixmap.height() * scale_factor)
                pixmap = pixmap.scaled(new_w, new_h)

            buf = QBuffer()
            buf.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buf, "JPEG", jpeg_quality)
            data = bytes(buf.data())
            buf.close()

            with frame_lock:
                current_frame = data
        except Exception as e:
            print(f"[!] Frame capture error: {e}")

        elapsed = time.time() - t_start
        target_delay = 1.0 / stream_fps
        sleep_time = max(0.005, target_delay - elapsed)
        time.sleep(sleep_time)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
<title>PC Desktop Screen Share - Ultra Zoom & Pan</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    overflow: hidden;
    user-select: none;
    -webkit-user-select: none;
    width: 100vw;
    height: 100vh;
  }
  header {
    background: rgba(15, 23, 42, 0.92);
    backdrop-filter: blur(12px);
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    z-index: 1000;
    border-bottom: 1px solid rgba(56, 189, 248, 0.2);
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    transition: transform 0.3s ease;
  }
  header.hidden { transform: translateY(-100%); }
  .title {
    font-size: 14px;
    font-weight: 700;
    color: #38bdf8;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .badge {
    background: #059669;
    color: white;
    font-size: 10px;
    padding: 2px 7px;
    border-radius: 4px;
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .controls { display: flex; gap: 6px; align-items: center; }
  button {
    background: #1e293b;
    border: 1px solid #334155;
    color: #f1f5f9;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  button:hover { background: #334155; border-color: #38bdf8; }
  button.active { background: #0284c7; border-color: #38bdf8; color: white; }
  
  #viewport {
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    position: relative;
    cursor: grab;
    background: #050811;
  }
  #viewport:active { cursor: grabbing; }

  #stream-wrapper {
    position: absolute;
    top: 0;
    left: 0;
    transform-origin: 0 0;
    will-change: transform;
    transition: filter 0.2s ease;
  }

  #stream {
    display: block;
    pointer-events: none;
    image-rendering: -webkit-optimize-contrast;
  }

  /* Text Sharpening Filter for Google Assistant & Eye-Care */
  .mode-sharp #stream {
    filter: contrast(135%) brightness(105%) saturate(110%);
  }
  .mode-warm #stream {
    filter: sepia(30%) contrast(110%) brightness(95%);
  }
  .mode-highcontrast #stream {
    filter: contrast(160%) brightness(110%);
  }

  .hud {
    position: fixed;
    bottom: 16px;
    right: 16px;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid #334155;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 11px;
    color: #94a3b8;
    z-index: 999;
    pointer-events: none;
  }

  .hint-banner {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(30, 41, 59, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid #38bdf8;
    color: #f8fafc;
    padding: 10px 20px;
    border-radius: 30px;
    font-size: 13px;
    font-weight: 500;
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
    pointer-events: none;
    transition: opacity 0.5s ease;
    text-align: center;
    z-index: 1001;
  }
</style>
</head>
<body>
<header id="header">
  <div class="title">
    <span>💻 PC Desktop Stream</span>
    <span class="badge">LIVE</span>
  </div>
  <div class="controls">
    <button onclick="snapFit()" id="btn-fit" class="active" title="Fit Entire Screen">Fit</button>
    <button onclick="snap100()" id="btn-100" title="100% 1:1 Pixel Sharp">1:1</button>
    <button onclick="snapWidth()" id="btn-width" title="Fit Width for Reading">Width</button>
    <button onclick="cycleFilter()" id="btn-filter" title="Toggle Text Sharpening">👓 Sharp</button>
    <button onclick="toggleFullscreen()" title="Toggle Fullscreen">⛶</button>
    <button onclick="toggleHeader()" title="Hide Toolbar">▲</button>
  </div>
</header>

<div id="viewport" onwheel="handleWheel(event)" onmousedown="startDrag(event)" onmousemove="doDrag(event)" onmouseup="endDrag(event)" onmouseleave="endDrag(event)" ontouchstart="handleTouchStart(event)" ontouchmove="handleTouchMove(event)" ontouchend="handleTouchEnd(event)" ondblclick="handleDblClick(event)">
  <div id="stream-wrapper">
    <img id="stream" src="/stream" alt="PC Desktop Stream" onload="initDimensions()" />
  </div>
</div>

<div class="hud" id="hud">Zoom: 100% • Drag to Pan</div>

<div id="hint" class="hint-banner">
  ✨ Ready: Ask Google Assistant "What's on my screen?" (Mouse wheel to zoom, drag to pan)
</div>

<script>
  let scale = 1.0;
  let panX = 0;
  let panY = 0;
  let isDragging = false;
  let startX = 0, startY = 0;
  let imgW = 1920, imgH = 1080;
  let filterState = 0; // 0=normal, 1=sharp, 2=highcontrast, 3=warm

  const wrapper = document.getElementById('stream-wrapper');
  const img = document.getElementById('stream');
  const viewport = document.getElementById('viewport');
  const header = document.getElementById('header');
  const hud = document.getElementById('hud');
  const hint = document.getElementById('hint');

  setTimeout(() => { if (hint) hint.style.opacity = '0'; }, 6000);

  function initDimensions() {
    if (img.naturalWidth) {
      imgW = img.naturalWidth;
      imgH = img.naturalHeight;
      snapFit();
    }
  }

  function updateTransform() {
    wrapper.style.transform = `translate(${panX}px, ${panY}px) scale(${scale})`;
    hud.innerText = `Zoom: ${Math.round(scale * 100)}% | X: ${Math.round(panX)} Y: ${Math.round(panY)}`;
  }

  function snapFit() {
    const vw = viewport.clientWidth;
    const vh = viewport.clientHeight;
    scale = Math.min(vw / imgW, vh / imgH);
    panX = (vw - imgW * scale) / 2;
    panY = (vh - imgH * scale) / 2;
    updateTransform();
    setActiveBtn('btn-fit');
  }

  function snap100() {
    const vw = viewport.clientWidth;
    const vh = viewport.clientHeight;
    scale = 1.0;
    panX = (vw - imgW) / 2;
    panY = (vh - imgH) / 2;
    updateTransform();
    setActiveBtn('btn-100');
  }

  function snapWidth() {
    const vw = viewport.clientWidth;
    scale = vw / imgW;
    panX = 0;
    panY = 50;
    updateTransform();
    setActiveBtn('btn-width');
  }

  function setActiveBtn(id) {
    ['btn-fit', 'btn-100', 'btn-width'].forEach(b => {
      const el = document.getElementById(b);
      if (el) el.classList.toggle('active', b === id);
    });
  }

  function handleWheel(e) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;
    const mouseX = e.clientX;
    const mouseY = e.clientY;

    const newScale = Math.min(Math.max(0.2, scale * zoomFactor), 6.0);
    // Zoom centered at mouse cursor
    panX = mouseX - (mouseX - panX) * (newScale / scale);
    panY = mouseY - (mouseY - panY) * (newScale / scale);
    scale = newScale;
    updateTransform();
    setActiveBtn('');
  }

  function startDrag(e) {
    isDragging = true;
    startX = e.clientX - panX;
    startY = e.clientY - panY;
  }

  function doDrag(e) {
    if (!isDragging) return;
    panX = e.clientX - startX;
    panY = e.clientY - startY;
    updateTransform();
  }

  function endDrag() {
    isDragging = false;
  }

  function handleDblClick(e) {
    if (scale < 0.95) {
      snap100();
    } else {
      snapFit();
    }
  }

  // Touch Support (Pinch zoom & pan)
  let initialDist = null;
  let initialScale = 1.0;

  function handleTouchStart(e) {
    if (e.touches.length === 1) {
      isDragging = true;
      startX = e.touches[0].clientX - panX;
      startY = e.touches[0].clientY - panY;
    } else if (e.touches.length === 2) {
      isDragging = false;
      initialDist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      initialScale = scale;
    }
  }

  function handleTouchMove(e) {
    if (e.touches.length === 1 && isDragging) {
      panX = e.touches[0].clientX - startX;
      panY = e.touches[0].clientY - startY;
      updateTransform();
    } else if (e.touches.length === 2 && initialDist) {
      const dist = Math.hypot(
        e.touches[0].clientX - e.touches[1].clientX,
        e.touches[0].clientY - e.touches[1].clientY
      );
      scale = Math.min(Math.max(0.2, initialScale * (dist / initialDist)), 6.0);
      updateTransform();
    }
  }

  function handleTouchEnd() {
    isDragging = false;
    initialDist = null;
  }

  function cycleFilter() {
    filterState = (filterState + 1) % 4;
    document.body.className = '';
    const btn = document.getElementById('btn-filter');
    if (filterState === 1) {
      document.body.classList.add('mode-sharp');
      btn.innerText = '👓 Sharp';
      btn.classList.add('active');
    } else if (filterState === 2) {
      document.body.classList.add('mode-highcontrast');
      btn.innerText = '⚡ Contrast';
      btn.classList.add('active');
    } else if (filterState === 3) {
      document.body.classList.add('mode-warm');
      btn.innerText = '💡 Warm';
      btn.classList.add('active');
    } else {
      btn.innerText = 'Normal';
      btn.classList.remove('active');
    }
  }

  function toggleHeader() {
    header.classList.toggle('hidden');
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  window.addEventListener('resize', snapFit);
</script>
</body>
</html>
"""

class StreamHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # Quiet logging

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=--frame")
            self.send_header("Cache-Control", "no-cache, private")
            self.send_header("Pragma", "no-cache")
            self.end_headers()

            while is_streaming:
                with frame_lock:
                    frame = current_frame

                if frame:
                    try:
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii"))
                        self.wfile.write(frame)
                        self.wfile.write(b"\r\n")
                    except (BrokenPipeError, ConnectionResetError):
                        break
                time.sleep(1.0 / stream_fps)

        elif path == "/snapshot":
            with frame_lock:
                frame = current_frame
            if frame:
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(frame)))
                self.end_headers()
                self.wfile.write(frame)
            else:
                self.send_error(503, "No frame available yet")
        else:
            self.send_error(404, "Not found")

class ThreadedHTTPServer(HTTPServer):
    """Serve requests in separate threads for streaming."""
    pass

def setup_adb_forward():
    """Sets up ADB reverse port forwarding and launches Chrome on phone."""
    print(f"[*] Setting up ADB reverse tunnel (tcp:{PORT} -> tcp:{PORT})...")
    try:
        subprocess.run([ADB_PATH, "reverse", f"tcp:{PORT}", f"tcp:{PORT}"], capture_output=True, text=True)
        print("[+] ADB reverse tunnel established successfully.")
    except Exception as e:
        print(f"[!] ADB reverse failed: {e}")

    print("[*] Opening stream in Android browser...")
    url = f"http://localhost:{PORT}"
    try:
        cmd = [ADB_PATH, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print("[+] Android browser opened to desktop stream.")
        else:
            print(f"[!] Android intent failed: {res.stderr.strip()}")
    except Exception as e:
        print(f"[!] Launch intent error: {e}")

def start_stream_server(port=PORT):
    global is_streaming
    ensure_qapp()
    is_streaming = True

    capture_thread = threading.Thread(target=screen_capture_loop, daemon=True)
    capture_thread.start()

    server = ThreadedHTTPServer(("0.0.0.0", port), StreamHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    local_ip = get_local_ip()
    print("=" * 60)
    print("  🚀 PC Screen Streamer for Mobile Google Assistant Active!")
    print(f"  - USB / Tunnel URL:  http://localhost:{port}")
    print(f"  - Wi-Fi Local URL:   http://{local_ip}:{port}")
    print("=" * 60)

    # Tunnel & launch on device
    setup_adb_forward()
    return server

def stop_stream_server(server=None):
    global is_streaming
    is_streaming = False
    if server:
        server.shutdown()
        server.server_close()
    try:
        subprocess.run([ADB_PATH, "reverse", "--remove", f"tcp:{PORT}"], capture_output=True)
    except Exception:
        pass
    print("[*] Screen streamer stopped.")

if __name__ == "__main__":
    server = start_stream_server(PORT)
    print("\nPress Ctrl+C to stop streaming.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        stop_stream_server(server)

# PirateLibrary for Raspberry Pi Zero W
# Setup script in Python with captive portal, file server UI, settings menu, and auto-start

import os
import subprocess
import json
from http.server import SimpleHTTPRequestHandler, HTTPServer
import socket
import threading
from urllib.parse import unquote
from io import BytesIO

# Paths
CONFIG_FILE = "/home/pi/piratelibrary/piratelibrary.conf"
DEFAULT_DIR = "/home/pi/piratelibrary/files"
USB_MOUNT_POINT = "/media/usb"
PORT = 80

# Determine shared directory (USB if available)
if os.path.ismount(USB_MOUNT_POINT):
    SHARED_DIR = USB_MOUNT_POINT
else:
    SHARED_DIR = DEFAULT_DIR

# Load or initialize config
DEFAULT_CONFIG = {
    "ssid": "PirateLibrary",
    "password": "",
    "hostname": "PirateLibrary"
}
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(DEFAULT_CONFIG, f)
with open(CONFIG_FILE) as f:
    config = json.load(f)

SSID = config.get("ssid", DEFAULT_CONFIG["ssid"])
PASSWORD = config.get("password", DEFAULT_CONFIG["password"])

# Ensure shared directory exists
os.makedirs(SHARED_DIR, exist_ok=True)

# Custom HTTP Handler with upload and settings
class FileServerHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            files = os.listdir(SHARED_DIR)
            file_links = ''.join([f'<li><a href="/{file}">{file}</a></li>' for file in files])
            html = f"""
            <html><head><title>{SSID}</title></head>
            <body>
            <h1>Welcome to {SSID}</h1>
            <form ENCTYPE='multipart/form-data' method='POST'>
                <input name='file' type='file'/>
                <input type='submit' value='Upload'/>
            </form>
            <ul>{file_links}</ul>
            <a href="/settings">Settings</a>
            </body></html>
            """
            self.wfile.write(html.encode())

        elif self.path == "/settings":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = f"""
            <html><head><title>Settings</title></head>
            <body>
            <h2>Settings</h2>
            <form method='POST' action='/settings'>
                SSID: <input type='text' name='ssid' value='{SSID}'/><br>
                Password (optional): <input type='text' name='password' value='{PASSWORD}'/><br>
                <input type='submit' value='Save'/>
            </form>
            <a href="/">Back to Home</a>
            </body></html>
            """
            self.wfile.write(html.encode())

        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/settings":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            params = dict(pair.split('=') for pair in post_data.split('&'))
            new_ssid = unquote(params.get("ssid", SSID))
            new_password = unquote(params.get("password", PASSWORD))
            new_config = {
                "ssid": new_ssid,
                "password": new_password,
                "hostname": new_ssid
            }
            with open(CONFIG_FILE, 'w') as f:
                json.dump(new_config, f)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            html = """
            <html><body><h3>Settings saved. Please reboot to apply changes.</h3>
            <a href="/">Back to Home</a>
            </body></html>
            """
            self.wfile.write(html.encode())
        else:
            content_length = int(self.headers['Content-Length'])
            boundary = self.headers['Content-Type'].split("=")[1].encode()
            body = self.rfile.read(content_length)
            parts = body.split(b"--" + boundary)
            for part in parts:
                if b"Content-Disposition" in part:
                    headers, file_data = part.split(b"\r\n\r\n", 1)
                    file_data = file_data.rsplit(b"\r\n", 1)[0]
                    filename_line = headers.decode().split("\r\n")[0]
                    filename = filename_line.split("filename=")[1].strip('"')
                    filepath = os.path.join(SHARED_DIR, filename)
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

# File Server Thread
def run_file_server():
    os.chdir(SHARED_DIR)
    server = HTTPServer(("0.0.0.0", PORT), FileServerHandler)
    print(f"[*] Serving files and upload form on port {PORT}")
    server.serve_forever()

# Setup Access Point (AP) and DHCP server
def setup_router():
    print("[*] Setting up access point...")

    hostapd_conf = f"""
interface=wlan0
driver=nl80211
ssid={SSID}
hw_mode=g
channel=6
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
    """
    if PASSWORD:
        hostapd_conf += f"""
wpa=2
wpa_passphrase={PASSWORD}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
        """

    with open("/etc/hostapd/hostapd.conf", "w") as f:
        f.write(hostapd_conf)

    dnsmasq_conf = f"""
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
address=/#/192.168.4.1
    """
    with open("/etc/dnsmasq.conf", "w") as f:
        f.write(dnsmasq_conf)

    subprocess.run(["sudo", "ifconfig", "wlan0", "192.168.4.1"])
    subprocess.run(["sudo", "systemctl", "start", "hostapd"])
    subprocess.run(["sudo", "systemctl", "start", "dnsmasq"])
    print("[*] Access point and DHCP server should be running.")

# Add autostart service
def setup_autostart():
    service_content = f"""
[Unit]
Description=PirateLibrary Service
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/piratelibrary/piratelibrary.py
WorkingDirectory=/home/pi/piratelibrary
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
    """
    os.makedirs("/home/pi/.config/systemd/user", exist_ok=True)
    with open("/etc/systemd/system/piratelibrary.service", "w") as f:
        f.write(service_content)
    subprocess.run(["sudo", "systemctl", "enable", "piratelibrary"])
    print("[*] Auto-start service installed.")

if __name__ == "__main__":
    threading.Thread(target=run_file_server, daemon=True).start()
    setup_router()
    setup_autostart()
    print(f"[*] PirateLibrary is up. Serving from: {SHARED_DIR}")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")

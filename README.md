# PirateLibrary

**PirateLibrary** is a self-hosted, standalone Wi-Fi file server designed for Raspberry Pi Zero W (and other Raspberry Pi models). It creates its own wireless access point with a captive portal, allowing connected users to browse, upload, and download files from an attached USB storage device or internal storage — all managed through an easy-to-use web interface.

---

## Features

- **Standalone Wi-Fi Access Point**: Automatically sets up a wireless hotspot named "PirateLibrary" (default), with configurable SSID and password.
- **Captive Portal**: Browser requests automatically redirect to the file server’s homepage, providing a seamless user experience.
- **File Server with Upload/Download**: Users can upload and download files via a clean, mobile-friendly web interface.
- **USB Storage Support**: Automatically detects and serves files from an attached USB drive mounted at `/media/usb`. Falls back to internal storage if no USB is found.
- **Settings Panel**: Allows hosts to change SSID, password, and view storage details directly from the web interface.
- **Auto-start on Boot**: Installs a systemd service to start PirateLibrary automatically on system startup.
- **Headless Operation**: Designed to run without monitor or keyboard — manage everything via the Wi-Fi network.

---

## Requirements

- Raspberry Pi Zero W or any Raspberry Pi with Wi-Fi.
- Raspberry Pi OS (Lite recommended for headless use).
- Python 3.x
- `hostapd` and `dnsmasq` installed and configured.
- USB storage device (optional, but recommended for larger file libraries).

---

## Installation

1. **Prepare your Raspberry Pi** with Raspberry Pi OS Lite.

2. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install hostapd dnsmasq python3
   sudo systemctl stop hostapd
   sudo systemctl stop dnsmasq

# Clone the PirateLibrary repo to your Pi:
git clone https://github.com/yourusername/piratelibrary.git /home/pi/piratelibrary
cd /home/pi/piratelibrary

## Run the main script once:
sudo python3 piratelibrary.py


## Reboot your Pi:
sudo reboot


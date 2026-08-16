# 🔍 OSINT Threat Intelligence Scanner

An Open Source Intelligence (OSINT) and Threat Intelligence tool developed in Python, specifically optimised to run on Android terminals via Termux.

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [What's New in V1.1.0](#-whats-new-in-v110)
- [Key Features](#-key-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Contributing](#-contributing)
- [Legal Disclaimer](#-legal-disclaimer)

## 📄 About the Project

This tool focuses on the investigation of digital profiles: emails, usernames, phone numbers, domains, and leaked passwords. It aggregates multiple free APIs and scraping techniques into a single, lightweight terminal interface, and automatically verifies its own environment at startup.

## 🆕 What's New in V1.1.0

- **Dark Web Deep Scan** — searches the target on Ahmia.fi (public `.onion` index) and generates dark web-focused verification links.
- **Automatic Tor detection** — detects a local Tor client (daemon on port 9050 or Tor Browser on 9150) at startup and during every investigation; the status is recorded in the report. With Tor connected, the scan queries Ahmia's `.onion` endpoint routed through SOCKS5.
- **Automatic dependency installation** — missing Python packages are installed via pip at startup, with no user interaction.
- **Secure API key handling** — the IntelX key is no longer hard-coded: it is requested at first launch (validated UUID format, saved to `config.json`) or supplied via the `INTELX_KEY` environment variable.
- **Entropy heuristic** — the Fake Profile Scanner now flags random-looking, machine-generated identifiers using Shannon entropy.
- **Simplified menu** — database updates and dependency checks now run automatically at startup.

## ⭐ Key Features

- **Auto-Updating DB** — automatically downloads the latest list of 400+ social networks from the Sherlock Project (cached for 7 days).
- **📧 Email OSINT** — Holehe, Gravatar (profile picture and real name), EmailRep (reputation check), and Google Dorks.
- **👤 Username OSINT** — simultaneous checking across 400+ sites using threading, Namechk, and Wayback Machine history.
- **📱 Phone OSINT** — generates direct links for WhatsApp, Telegram, Truecaller, and tailored Google Dorks.
- **🌐 Domain OSINT** — subdomain discovery via certificate transparency (crt.sh).
- **🕵️ Fake Profile Scanner** — heuristic risk scoring (0–100) for fake, throwaway or bot accounts.
- **🌑 Dark Web Scan** — Ahmia.fi search with automatic Tor routing when a Tor client is available.
- **🔍 Leak & Threat Intel** — Pastebin scraping, GitHub code search, and HIBP password check (k-anonymity).
- **📋 Report Management** — automatically generates clean `.txt` files containing the results of each analysis, including the Tor status.

## ⚠️ Installation

> **Warning:** Do not download Termux from the Google Play Store (it is outdated). Please use [F-Droid](https://f-droid.org/) or the official GitHub releases.

# Open Termux and update the system:
pkg update && pkg upgrade -y

# Install Python and Git:
pkg install python git -y

# Clone this repository:
git clone https://github.com/carlosbarrosovieira/osint-scanner
cd osint-scanner

# Run the application (dependencies are installed automatically on first launch):
python osint_mobile.py
Optional — for the advanced dark web scan via Tor:


bash
pkg install tor
tor &
The application detects the Tor client automatically (ports 9050/9150). Without Tor, it runs in clearnet mode and notes the limitation in the report.

💻 Usage
To start the application, run:


bash
python osint_mobile.py
On first launch you may optionally provide an IntelX API key (get one at intelx.io); press Enter to skip. Then simply choose Search from the menu and enter a target: an email address, username, phone number, domain, or password. Every investigation is saved as a timestamped .txt report, which can be viewed or deleted from the Manage Reports menu.

🤝 Contributing
This project is under active development, and community help is highly appreciated! If you are a developer or a cybersecurity enthusiast, you can help by:

Reporting Bugs: open an Issue on GitHub describing the error.
Suggesting New APIs: do you know a free OSINT API? Suggest it in the Issues section!
Improving the Code: fork the project, make your changes, and open a Pull Request.
Areas where we need help:

Integration with Threat Intel APIs (e.g., Shodan, VirusTotal, AbuseIPDB).
Improving the scraping engine for exposed configuration files.
Speed optimisation for older Android devices.

****⚠️ Legal Disclaimer**
This tool was developed for educational purposes, penetration testing, and verifying your own digital footprint. Do not use it for stalking, harassment, or any illegal activities. The user is solely responsible for how they use this application.**

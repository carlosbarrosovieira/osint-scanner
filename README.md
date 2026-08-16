# 🔍 OSINT Threat Intelligence Scanner

An Open Source Intelligence (OSINT) and Threat Intelligence tool developed in Python, specifically optimised to run on Android terminals via Termux.

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [What's New in V1.2.0](#-whats-new-in-v120)
- [Key Features](#-key-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Contributing](#-contributing)
- [Legal Disclaimer](#-legal-disclaimer)

## 📄 About the Project

This tool focuses on the investigation of digital profiles: emails, usernames, phone numbers, domains, and leaked passwords. It aggregates multiple free APIs and scraping techniques into a single, lightweight terminal interface, automatically verifies its own environment at startup, and concludes every investigation with an aggregated Digital Exposure Score.

## 🆕 What's New in V1.2.0

- **SQLite response cache with TTL** — platform checks, DNS lookups and supported API responses are cached locally, making repeated investigations of the same target dramatically faster.
- **Network hardening** — thread-safe rate limiting (protects rate-limited APIs such as EmailRep), real browser User-Agent rotation, and exponential backoff retries.
- **Email DNS & spoofing analysis (keyless)** — MX record resolution (detects addresses that cannot receive mail) plus SPF, DKIM and DMARC checks to grade the domain's spoofing risk.
- **Offline phone intelligence** — number parsing with the `phonenumbers` library: validity, country, carrier, approximate location and line type (mobile/fixed/VoIP), with no API keys and no network calls.
- **Domain security headers audit (keyless)** — checks HSTS, Content-Security-Policy, X-Content-Type-Options, X-Frame-Options and Referrer-Policy over HTTPS, with a 0–100 security score.
- **JSON report export** — every investigation now saves a structured `.json` report alongside the plain-text one, with machine-readable results per module.
- **Digital Exposure Score** — an aggregated 0–100 score (LOW/MEDIUM/HIGH) combining footprint size, leak exposure, dark web leads and fake-profile indicators, with a full breakdown of contributing factors.

## ⭐ Key Features

- **Auto-Updating DB** — automatically downloads the latest list of 400+ social networks from the Sherlock Project (cached for 7 days).
- **⚡ Performance & Stealth** — SQLite response cache, request rate limiting, User-Agent rotation and exponential backoff retries.
- **📧 Email OSINT** — Holehe, Gravatar (profile picture and real name), EmailRep (reputation check), DNS analysis (MX/SPF/DKIM/DMARC spoofing risk), and Google Dorks.
- **👤 Username OSINT** — simultaneous checking across 400+ sites using threading, Namechk, and Wayback Machine history.
- **📱 Phone OSINT** — offline number analysis (validity, country, carrier, line type), plus direct links for WhatsApp, Telegram, Truecaller, and tailored Google Dorks.
- **🌐 Domain OSINT** — subdomain discovery via certificate transparency (crt.sh) and a keyless HTTP security headers audit (HSTS, CSP and more).
- **🕵️ Fake Profile Scanner** — heuristic risk scoring (0–100) for fake, throwaway or bot accounts, including Shannon entropy analysis.
- **🌑 Dark Web Scan** — Ahmia.fi search with automatic Tor routing when a Tor client is available.
- **🔍 Leak & Threat Intel** — Pastebin scraping, GitHub code search, and HIBP password check (k-anonymity).
- **🧮 Digital Exposure Score** — aggregated assessment across all modules with a contributing-factors breakdown.
- **📋 Report Management** — automatically generates clean `.txt` and structured `.json` files for each analysis, including the Tor status.

## ⚠️ Installation

> **Warning:** Do not download Termux from the Google Play Store (it is outdated). Please use [F-Droid](https://f-droid.org/) or the official GitHub releases.

```bash
# Open Termux and update the system:
pkg update && pkg upgrade -y

# Install Python and Git:
pkg install python git -y

# Clone this repository:
git clone https://github.com/carlosbarrosovieira/osint-scanner
cd osint-scanner

# Run the application (all dependencies, including dnspython and
# phonenumbers, are installed automatically on first launch):
python osint_mobile.py
```

Optional — for the advanced dark web scan via Tor:

```bash
pkg install tor
tor &
```

The application detects the Tor client automatically (ports 9050/9150). Without Tor, it runs in clearnet mode and notes the limitation in the report.

## 💻 Usage

To start the application, run:

```bash
python osint_mobile.py
```

On first launch you may optionally provide an IntelX API key (get one at [intelx.io](https://intelx.io)); press Enter to skip. Then simply choose **Search** from the menu and enter a target: an email address, username, phone number, domain, or password. Every investigation ends with a Digital Exposure Score and is saved as a timestamped `.txt` report plus a structured `.json` report, both viewable from the **Manage Reports** menu.

## 🤝 Contributing

This project is under active development, and community help is highly appreciated! If you are a developer or a cybersecurity enthusiast, you can help by:

1. **Reporting Bugs:** open an Issue on GitHub describing the error.
2. **Suggesting New APIs:** do you know a free OSINT API? Suggest it in the Issues section!
3. **Improving the Code:** fork the project, make your changes, and open a Pull Request.

Areas where we need help:

- Integration with Threat Intel APIs (e.g., Shodan, VirusTotal, AbuseIPDB).
- Improving the scraping engine for exposed configuration files.
- Speed optimisation for older Android devices.

## ⚠️ Legal Disclaimer

This tool was developed for educational purposes, penetration testing, and verifying your own digital footprint. Do not use it for stalking, harassment, or any illegal activities. The user is solely responsible for how they use this application.

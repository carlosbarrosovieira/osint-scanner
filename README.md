**🕵️ OSINT Threat Intelligence Scanner**
An Open Source Intelligence (OSINT) and Threat Intelligence tool developed in Python, specifically optimised to run on Android terminals via Termux.

PythonPlatformStatusLicense

**📋 Table of Contents**
About the Project
Key Features
Installation
Usage
Contributing
Legal Disclaimer

**📖 About the Project**
This tool focuses on the investigation of digital profiles: emails, usernames, phone numbers, domains, and leaked passwords. It aggregates multiple free APIs and scraping techniques into a single, lightweight terminal interface.

**✨ Key Features**
Module	Description
🤖 Auto-Updating DB	Automatically downloads the latest list of 300+ social networks from the Sherlock Project.
📧 Email OSINT	Holehe, Gravatar (extracts profile picture and real name), EmailRep (reputation check), and Google Dorks.
👤 Username OSINT	Simultaneous checking across 300+ sites using Threading, Namechk, and Wayback Machine history.
📱 Phone OSINT	Generates direct links for WhatsApp, Telegram, Truecaller, and tailored Google Dorks.
🩸 Leak & Threat Intel	Pastebin scraping, GitHub code search, HudsonRock API (Info-Stealers), and HIBP password check.
📄 Report Management	Automatically generates clean .txt files containing the results of each analysis.

**📦 Installation** 
**⚠️ Warning:** Do not download Termux from the Google Play Store (it is outdated). Please use F-Droid or the official GitHub releases.

**1 - Open Termux and update the system:**
    pkg update && pkg upgrade -y
    
**2 - Install Python and Git:**
    pkg install python git -y

**3 - Install Python dependencies:**
    pip install requests colorama holehe

**4 - Clone this repository:**
    git clone https://github.com/scartPT/osint-scanner.git
    cd osint-scanner

**💻 Usage**
To start the application, run:
python osint_mobile.py

**🤝 Contributing**
This project is under active development, and community help is highly appreciated! If you are a developer or a cybersecurity enthusiast, you can help by:
1 - Reporting Bugs: Open an Issue on GitHub describing the error.
2 - Suggesting New APIs: Do you know a free OSINT API? Suggest it in the Issues section!
3 - Improving the Code: Fork the project, make your changes, and open a Pull Request.

**Areas where we need help:**
. Integration with Threat Intel APIs (e.g., Shodan, VirusTotal, AbuseIPDB).
. Improving the scraping engine for exposed configuration files.
. Speed optimisation for older Android devices.

**⚠️ Legal Disclaimer**
This tool was developed for educational purposes, penetration testing, and verifying your own digital footprint. Do not use it for stalking, harassment, or any illegal activities. The user is solely responsible for how they use this application.


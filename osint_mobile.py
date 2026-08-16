cat << 'EOF' > osint_mobile.py
#!/usr/bin/env python3
import os
import sys
import subprocess
import requests
import hashlib
import json
import time
import datetime
import re
import concurrent.futures
import glob
import shutil
from colorama import init, Fore

init(autoreset=True)

# ============================================================
# CONFIGURATION AND INITIALISATION
# ============================================================

ANSI_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def load_config():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        config = {"intelx_key": "a8dcda2c-ba08-4fd4-8a7c-f9a67f4e2e2a"}
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except:
        return {"intelx_key": ""}

config = load_config()
report_buffer = []
platforms_db = {}

def log_print(text):
    print(text)
    clean_text = ANSI_RE.sub('', text)
    report_buffer.append(clean_text)

# ============================================================
# UTILITIES AND DESIGN
# ============================================================

def print_dynamic_box(lines):
    w = 48
    log_print(f"{Fore.CYAN}╔{'═' * (w-2)}╗")
    for line in lines:
        clean = ANSI_RE.sub('', line)
        padding = max(0, w - 2 - len(clean) - 2)
        log_print(f"{Fore.CYAN}║ {line}{' ' * padding}{Fore.CYAN} ║")
    log_print(f"{Fore.CYAN}╚{'═' * (w-2)}╝")

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_section(title):
    print(f"\n{Fore.MAGENTA}┌─── {Fore.WHITE}{title} {Fore.MAGENTA}───")

def print_progress(iteration, total, bar_length=25):
    percent = min(100 * (iteration / float(total)), 100)
    filled = int(bar_length * iteration // total)
    bar = '█' * filled + '░' * (bar_length - filled)
    sys.stdout.write(f'\r{Fore.YELLOW}🔄 Progress: |{bar}| {percent:.1f}% ')
    sys.stdout.flush()
    if iteration >= total:
        print()

def robust_http_get(url, headers=None, timeout=8, retries=3):
    for attempt in range(retries):
        try:
            return requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        except requests.exceptions.RequestException:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                return None

def format_timestamp(ts):
    try:
        if ts > 1000000000000:
            ts = ts / 1000
        return datetime.datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
    except:
        return "Unknown date"

def is_email(target):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', target) is not None

def is_domain(target):
    return re.match(r'^((?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,6}$', target) is not None

def is_phone(target):
    digits = re.sub(r'\D', '', target)
    return len(digits) >= 8 and len(digits) <= 15 and not is_email(target) and not is_domain(target)

# ============================================================
# AUTO-UPDATING PLATFORM DATABASE + WATCHDOG
# ============================================================

def load_or_update_platforms(force=False):
    global platforms_db
    cache_file = 'platforms_cache.json'

    if not force and os.path.exists(cache_file):
        mod_time = os.path.getmtime(cache_file)
        if (time.time() - mod_time) < 7 * 24 * 60 * 60:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    platforms_db = json.load(f)
                return
            except:
                pass

    print(f"{Fore.YELLOW}Updating platform database from Sherlock Project...")

    urls = [
        "https://cdn.jsdelivr.net/gh/sherlock-project/sherlock@master/sherlock_project/resources/data.json",
        "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock_project/resources/data.json",
        "https://cdn.jsdelivr.net/gh/sherlock-project/sherlock@master/sherlock/resources/data.json",
        "https://raw.githubusercontent.com/sherlock-project/sherlock/master/sherlock/resources/data.json"
    ]
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    downloaded = False
    for url in urls:
        resp = robust_http_get(url, headers=headers, timeout=20, retries=2)
        if resp and resp.status_code == 200:
            try:
                parsed = resp.json()
                if isinstance(parsed, dict) and len(parsed) > 10:
                    platforms_db = parsed
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(platforms_db, f, indent=4)
                    print(f"{Fore.GREEN}[+] Database updated with {len(platforms_db)} platforms.")
                    time.sleep(1)
                    downloaded = True
                    break
            except:
                pass

    if not downloaded:
        print(f"{Fore.RED}[!] Failed to download database. Using built-in list.")
        platforms_db = {
            'GitHub': {'url': 'https://api.github.com/users/{}', 'errorType': 'status_code', 'errorCode': 404},
            'Instagram': {'url': 'https://www.instagram.com/{}/', 'errorType': 'message', 'errorMsg': 'Sorry, this page'},
            'Twitter/X': {'url': 'https://nitter.net/{}', 'errorType': 'message', 'errorMsg': 'User not found'},
            'Reddit': {'url': 'https://www.reddit.com/user/{}', 'errorType': 'message', 'errorMsg': 'Nobody on Reddit goes by that name'},
            'Facebook': {'url': 'https://www.facebook.com/{}', 'errorType': 'message', 'errorMsg': 'This page isn\'t available'},
            'TikTok': {'url': 'https://www.tiktok.com/@{}', 'errorType': 'message', 'errorMsg': 'Couldn\'t find this account'},
            'YouTube': {'url': 'https://www.youtube.com/@{}', 'errorType': 'message', 'errorMsg': 'This channel does not exist'},
            'Steam': {'url': 'https://steamcommunity.com/id/{}', 'errorType': 'message', 'errorMsg': 'The specified profile could not be found'},
            'Pinterest': {'url': 'https://www.pinterest.com/{}/', 'errorType': 'message', 'errorMsg': 'Sorry, we couldn\'t find that page'},
            'Spotify': {'url': 'https://open.spotify.com/user/{}', 'errorType': 'status_code', 'errorCode': 404},
            'Twitch': {'url': 'https://www.twitch.tv/{}', 'errorType': 'message', 'errorMsg': 'User not found'}
        }

def watchdog_platforms():
    try:
        load_or_update_platforms()
    except KeyboardInterrupt:
        print(f"{Fore.RED}\n[!] Platform update interrupted by user.")
    except Exception as e:
        print(f"{Fore.RED}[!] Unexpected error updating platforms: {e}")

# ============================================================
# MODULE: PHONE
# ============================================================

def investigate_phone(number):
    print_section(f"📱 PHONE NUMBER INVESTIGATION: {number}")
    digits_only = re.sub(r'\D', '', number)

    print_section("🔍 DEEP SEARCH (GOOGLE DORKS)")
    log_print(f"  {Fore.YELLOW}Use the links in the browser to force Google to find data:\n")
    dorks = [
        ("General Search (Flexible)", f"https://www.google.com/search?q={digits_only}"),
        ("General Search (Exact)", f"https://www.google.com/search?q=%22{digits_only}%22"),
        ("Search in PDFs and Documents", f"https://www.google.com/search?q={digits_only}+filetype:pdf+OR+filetype:doc"),
        ("Search in Social Networks", f"https://www.google.com/search?q={digits_only}+site:facebook.com+OR+site:instagram.com+OR+site:linkedin.com"),
        ("Search in Pastebins/Leaks", f"https://www.google.com/search?q={digits_only}+site:pastebin.com+OR+site:reddit.com+OR+site:ghostbin.com")
    ]
    for name, url in dorks:
        log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} {name}:")
        log_print(f"     {Fore.BLUE}{url}")

    print_section("💬 MESSAGING APPS & CALLER ID")
    log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} WhatsApp (Check profile/photo):")
    log_print(f"     {Fore.BLUE}https://wa.me/{digits_only}")
    log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Telegram (Add by number):")
    log_print(f"     {Fore.BLUE}https://t.me/+{digits_only}")
    log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Truecaller (Account holder name):")
    log_print(f"     {Fore.BLUE}https://www.truecaller.com/search/pt/{digits_only}")
    log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Sync.me (Reputation & Spam):")
    log_print(f"     {Fore.BLUE}https://sync.me/search/?number={digits_only}")

# ============================================================
# MODULE: EMAIL
# ============================================================

def investigate_email(email):
    print_section(f"📧 EMAIL INVESTIGATION: {email}")
    TOTAL = 120
    found = []
    verified = 0

    try:
        proc = subprocess.Popen(['holehe', email], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print_progress(0, TOTAL)

        for line in proc.stdout:
            line = line.strip()
            if line.startswith(('[+]', '[-]')):
                verified += 1
                print_progress(min(verified, TOTAL), TOTAL)
                if line.startswith('[+]'):
                    site = line.replace('[+]', '').replace('email is used in', '').strip()
                    if site and 'Email not used' not in site:
                        found.append(f"  {Fore.GREEN}[✅]{Fore.WHITE} [Holehe] {Fore.CYAN}[Email]{Fore.WHITE} -> {Fore.YELLOW}{site}")

        proc.wait()
        print_progress(TOTAL, TOTAL)

        if found:
            log_print(f"\n{Fore.GREEN}[+] ASSOCIATED ACCOUNTS FOUND:\n")
            for s in found:
                log_print(s)
        else:
            log_print(f"\n{Fore.RED}  [❌] No public accounts found via Holehe API.")
    except FileNotFoundError:
        log_print(f"{Fore.RED}[!] Holehe not installed. Run: pip install holehe")
    except Exception as e:
        log_print(f"{Fore.RED}[!] Error running Holehe: {e}")

    print_section("👤 METADATA & IDENTITY (GRAVATAR)")
    clean_email = email.strip().lower()
    email_hash = hashlib.md5(clean_email.encode('utf-8')).hexdigest()

    grav_url = f"https://gravatar.com/{email_hash}.json"
    grav_resp = robust_http_get(grav_url, timeout=5, retries=1)
    if grav_resp and grav_resp.status_code == 200:
        try:
            entry = grav_resp.json()['entry'][0]
            display = entry.get('displayName', 'Unknown')
            bio = entry.get('aboutMe', 'No biography')
            log_print(f"  {Fore.GREEN}[✅]{Fore.WHITE} Real Name: {Fore.YELLOW}{display}")
            log_print(f"  {Fore.GREEN}[✅]{Fore.WHITE} Bio: {Fore.YELLOW}{bio}")
        except:
            pass

    log_print(f"  {Fore.CYAN}[📸]{Fore.WHITE} Profile Picture (Gravatar):")
    log_print(f"     {Fore.BLUE}https://www.gravatar.com/avatar/{email_hash}?s=400")

    print_section("🛡️ EMAIL REPUTATION (EMAILREP)")
    rep_url = f"https://emailrep.io/{email}"
    rep_resp = robust_http_get(rep_url, timeout=8, retries=1)
    if rep_resp and rep_resp.status_code == 200:
        try:
            data = rep_resp.json()
            reputation = data.get("reputation", "n/a")
            leaks = data.get("credentials_leaked", False)
            log_print(f"  {Fore.WHITE}Reputation: {Fore.YELLOW}{reputation}")
            if leaks:
                log_print(f"  {Fore.RED}[⚠️] Leaked credentials detected!")
        except:
            pass
    else:
        log_print(f"  {Fore.YELLOW}  [ℹ️] EmailRep rate limited the request.")

    print_section("🔍 DEEP SEARCH (GOOGLE DORKS)")
    log_print(f"  {Fore.YELLOW}Use the links in the browser to find data:\n")
    dorks = [
        ("General Search", f"https://www.google.com/search?q=%22{email}%22"),
        ("Email -> Username Correlation", f"https://www.google.com/search?q=%22{email}%22+inurl:profile+OR+intext:username+OR+intext:login"),
        ("Forums & Pastebins", f"https://www.google.com/search?q=%22{email}%22+site:pastebin.com+OR+site:reddit.com"),
        ("Config Files (Passwords)", f"https://www.google.com/search?q=%22{email}%22+filetype:env+OR+filetype:conf+OR+filetype:config"),
        ("Server Logs (Login Attempts)", f"https://www.google.com/search?q=%22{email}%22+filetype:log+intext:password+OR+intext:login")
    ]
    for name, url in dorks:
        log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} {name}:")
        log_print(f"     {Fore.BLUE}{url}")

# ============================================================
# MODULE: USERNAME (AUTO-UPDATED DATABASE)
# ============================================================

def check_platform_thread(name, data, username):
    if not isinstance(data, dict):
        return None
    url = data.get("url", "").replace("{}", username)
    if not url:
        return None

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    resp = robust_http_get(url, headers=headers, timeout=4, retries=1)
    if not resp:
        return None

    error_type = data.get("errorType")
    error_msg = data.get("errorMsg", "")
    error_code = data.get("errorCode", 404)

    try:
        if error_type == "status_code":
            if resp.status_code == error_code:
                return None
        elif error_type == "message":
            if error_msg and error_msg in resp.text:
                return None
        elif error_type == "response_url":
            if error_msg and error_msg in resp.url:
                return None

        return f"  {Fore.GREEN}[✅]{Fore.WHITE} [{name}] {Fore.CYAN}[Username]{Fore.WHITE} -> {Fore.YELLOW}{url}"
    except:
        return None

def investigate_username(username):
    print_section(f"👤 USERNAME INVESTIGATION: {username}")

    if not platforms_db:
        watchdog_platforms()

    found = []
    total = len(platforms_db)

    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = {executor.submit(check_platform_thread, name, data, username): name for name, data in platforms_db.items()}
        done = 0
        for future in concurrent.futures.as_completed(futures):
            done += 1
            print_progress(done, total)
            result = future.result()
            if result:
                found.append(result)

    print_progress(total, total)
    if found:
        log_print(f"\n{Fore.GREEN}[+] PROFILES FOUND:\n")
        for s in found:
            log_print(s)
    else:
        log_print(f"\n{Fore.RED}  [❌] No profiles found.")

    print_section("🌐 MASS VERIFICATION (NAMECHK)")
    log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Check availability across +100 sites:")
    log_print(f"     {Fore.BLUE}https://namechk.com/profile/{username}")

    print_section("🕰️ PROFILE HISTORY (WAYBACK MACHINE)")
    log_print(f"  {Fore.YELLOW}View old bios and photos of deleted profiles:\n")
    wayback = [
        ("Instagram (History)", f"https://web.archive.org/web/*/instagram.com/{username}/*"),
        ("Twitter/X (History)", f"https://web.archive.org/web/*/twitter.com/{username}/*"),
        ("Facebook (History)", f"https://web.archive.org/web/*/facebook.com/{username}/*")
    ]
    for name, url in wayback:
        log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} {name}:")
        log_print(f"     {Fore.BLUE}{url}")

# ============================================================
# MODULE: DOMAIN
# ============================================================

def investigate_domain(domain):
    print_section(f"🌐 DOMAIN INVESTIGATION: {domain}")
    resp = robust_http_get(f'https://crt.sh/?q=%25.{domain}&output=json', timeout=12, retries=2)
    if resp and resp.status_code == 200:
        try:
            data = resp.json()
            subdomains = set()
            for item in data:
                name = item.get('name_value', '')
                for n in name.split('\n'):
                    n = n.replace('*.', '').strip()
                    if n:
                        subdomains.add(n)
            if subdomains:
                log_print(f"\n  {Fore.GREEN}[✅]{Fore.WHITE} [crt.sh] {Fore.CYAN}[Subdomains]{Fore.WHITE} -> {Fore.YELLOW}Found {len(subdomains)} records:")
                for sub in list(subdomains)[:15]:
                    log_print(f"     {Fore.YELLOW}- {sub}")
            else:
                log_print(f"\n{Fore.RED}  [❌] No subdomains found.")
        except:
            log_print(f"\n{Fore.RED}  [❌] Error in crt.sh.")
    else:
        log_print(f"\n{Fore.RED}  [❌] No certificates found.")

# ============================================================
# MODULE: LEAKS & PASSWORDS
# ============================================================

def check_password_pwned(password):
    print_section("🔑 PASSWORD VERIFICATION (HIBP)")
    sha1 = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    resp = robust_http_get(f'https://api.pwnedpasswords.com/range/{prefix}', timeout=8, retries=3)
    if resp and resp.status_code == 200:
        for line in resp.text.splitlines():
            parts = line.split(':')
            if parts[0] == suffix:
                count = int(parts[1])
                log_print(f"  {Fore.RED}[⚠️]{Fore.WHITE} [HIBP] {Fore.CYAN}[Password]{Fore.WHITE} -> {Fore.RED}Leaked {count:,} times!")
                return True
    log_print(f"  {Fore.GREEN}[🛡️]{Fore.WHITE} [HIBP] {Fore.CYAN}[Password]{Fore.WHITE} -> {Fore.GREEN}Secure password.")
    return False

def check_hudson_rock(target):
    # Placeholder safe stub – no sensitive endpoints
    log_print(f"  {Fore.YELLOW}[ℹ️]{Fore.WHITE} HudsonRock-like check skipped (study mode).")

def check_free_credentials(target):
    print_section("🩸 PASSWORD SEARCH (FREE)")
    log_print(f"  {Fore.YELLOW}  [ℹ️] Use only public, legal sources.\n")

    links = [
        ("BreachDirectory (Free view)", f"https://breachdirectory.com/search?term={target}"),
        ("IntelX Web (Free preview)", f"https://intelx.io/?s={target}"),
        ("Google Dork: Databases (SQL)", f"https://www.google.com/search?q=%22{target}%22+filetype:sql+intext:password"),
        ("Google Dork: Text Files (TXT)", f"https://www.google.com/search?q=%22{target}%22+filetype:txt+intext:password"),
        ("Google Dork: Server Configs (ENV/JSON)", f"https://www.google.com/search?q=%22{target}%22+filetype:env+OR+filetype:json+intext:password"),
        ("Google Dork: Alternative Pastebins", f"https://www.google.com/search?q=%22{target}%22+site:ghostbin.com+OR+site:justpaste.it+intext:password")
    ]
    for name, url in links:
        log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} {name}:")
        log_print(f"     {Fore.BLUE}{url}")

def investigate_leaks(target, target_type):
    print_section(f"🔥 THREATS & PUBLIC LEAKS: {target}")
    found = []
    steps = 3
    print_progress(1, steps)

    gh = robust_http_get(f'https://api.github.com/search/code?q={target}', timeout=10, retries=1)
    try:
        if gh and gh.status_code == 200:
            for item in gh.json().get('items', [])[:5]:
                repo = item['repository']['full_name']
                link = item['html_url']
                found.append(f"  {Fore.RED}[⚠️]{Fore.WHITE} [GitHub] {Fore.CYAN}[{target_type}]{Fore.WHITE} -> {Fore.YELLOW}{repo} ({link})")
        elif gh and gh.status_code == 403:
            log_print(f"  {Fore.YELLOW}[⚠️] GitHub: API limit reached.")
    except:
        pass

    print_progress(2, steps)

    pb = robust_http_get(f'https://psbdmp.ws/api/search/{target}', timeout=10, retries=1)
    if pb and pb.status_code == 200:
        try:
            for item in pb.json()[:3]:
                pid = item.get('id')
                time_ts = item.get('time', 0)
                formatted_date = format_timestamp(time_ts)
                if pid:
                    url = f"https://pastebin.com/{pid}"
                    found.append(f"  {Fore.RED}[⚠️]{Fore.WHITE} [{formatted_date}] [Pastebin] {Fore.CYAN}[{target_type}]{Fore.WHITE} -> {Fore.YELLOW}{url}")
        except:
            pass

    print_progress(3, steps)

    if found:
        log_print(f"\n{Fore.RED}[!] PUBLIC LEAKS FOUND:\n")
        for s in found:
            log_print(s)
    else:
        log_print(f"\n{Fore.GREEN}  [🛡️] No automatic public leaks.")

    check_free_credentials(target)
    if not is_email(target) and not is_domain(target) and not is_phone(target):
        check_password_pwned(target)

# ============================================================
# FAKE PROFILE SCANNER (HEURISTIC, SAFE)
# ============================================================

def fake_profile_scanner(target, target_type):
    print_section(f"🕵️ FAKE PROFILE SCANNER: {target} ({target_type})")

    score = 0
    reasons = []

    t = target.strip()

    # Length heuristics
    if len(t) < 5:
        score += 20
        reasons.append("Very short identifier (possible throwaway or bot).")
    elif len(t) > 25:
        score += 10
        reasons.append("Very long identifier (may be auto-generated).")

    # Character mix
    if re.match(r'^[a-zA-Z0-9]+$', t):
        score += 5
        reasons.append("Only alphanumeric characters (common in autogenerated usernames).")
    if re.search(r'\d{4,}', t):
        score += 15
        reasons.append("Contains long numeric sequence (e.g., birth year or random ID).")
    if re.search(r'[_\.]{2,}', t):
        score += 10
        reasons.append("Multiple separators (underscore/dot) suggesting pattern-based creation.")

    # Email-specific heuristics
    if is_email(t):
        local, _, domain = t.partition('@')
        disposable_domains = [
            "mailinator.com", "10minutemail.com", "guerrillamail.com",
            "yopmail.com", "trashmail.com", "tempmail.com"
        ]
        if domain.lower() in disposable_domains:
            score += 40
            reasons.append(f"Disposable email domain detected: {domain}.")
        if len(local) <= 3:
            score += 15
            reasons.append("Very short local part in email (low-effort / throwaway).")
        if re.search(r'\d{3,}', local):
            score += 10
            reasons.append("Numeric-heavy local part (possible autogenerated account).")

    # Domain-specific heuristics
    if is_domain(t):
        if t.startswith("xn--"):
            score += 25
            reasons.append("Punycode domain (possible homograph attack / fake brand).")
        if "-" in t:
            score += 5
            reasons.append("Hyphenated domain (sometimes used in fake clones).")

    # Phone-specific heuristics
    if is_phone(t):
        digits_only = re.sub(r'\D', '', t)
        if len(digits_only) < 9:
            score += 10
            reasons.append("Short phone number (may be invalid or virtual).")
        if digits_only.startswith(("000", "111", "123")):
            score += 20
            reasons.append("Suspicious prefix in phone number (pattern-like).")

    # Username/password generic heuristics
    if not is_email(t) and not is_domain(t) and not is_phone(t):
        if re.search(r'(test|fake|demo|user|admin)', t, re.IGNORECASE):
            score += 25
            reasons.append("Contains generic words like test/fake/demo/user/admin.")
        if re.search(r'(bot|auto|system)', t, re.IGNORECASE):
            score += 25
            reasons.append("Contains bot/auto/system (possible automated account).")

        # Entropy heuristic: random-looking strings suggest generated accounts
        if len(t) >= 8:
            from collections import Counter
            import math
            freq = Counter(t.lower())
            entropy = -sum((c / len(t)) * math.log2(c / len(t)) for c in freq.values())
            if entropy > 4.2:
                score += 20
                reasons.append(f"High character entropy ({entropy:.2f} bits/char) — looks machine-generated.")

    # Normalize score
    if score > 100:
        score = 100

    if score >= 70:
        risk = f"{Fore.RED}HIGH RISK{Fore.WHITE}"
    elif score >= 40:
        risk = f"{Fore.YELLOW}MEDIUM RISK{Fore.WHITE}"
    else:
        risk = f"{Fore.GREEN}LOW RISK{Fore.WHITE}"

    log_print(f"  {Fore.WHITE}Heuristic Risk Score: {Fore.YELLOW}{score}/100 {Fore.WHITE}({risk})")

    if reasons:
        log_print(f"  {Fore.CYAN}Indicators:")
        for r in reasons:
            log_print(f"    - {Fore.WHITE}{r}")
    else:
        log_print(f"  {Fore.GREEN}No strong indicators of fake/low-trust profile detected.")

# ============================================================
# MODULE: DARK WEB DEEP SCAN (CLEARNET GATEWAYS ONLY, LEGAL)
# ============================================================

def dark_web_scan(target, target_type, tor_port=None):
    if tor_port:
        print_section(f"🌑 DARK WEB DEEP SCAN (VIA TOR): {target}")
        log_print(f"  {Fore.GREEN}[✅] Tor client CONNECTED — scanning through SOCKS5 (127.0.0.1:{tor_port}).")
    else:
        print_section(f"🌑 DARK WEB DEEP SCAN: {target}")
        log_print(f"  {Fore.RED}[❌] Tor client DISCONNECTED — clearnet mode only (limited results).")

    found = []
    steps = 3

    # --- 1. Ahmia.fi (clearnet or onion endpoint via Tor) ---
    print_progress(1, steps)
    if tor_port:
        ahmia_host = "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion"
        log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Searching Ahmia via Tor (onion endpoint)...")
        resp = tor_get(f"{ahmia_host}/search/?q={requests.utils.quote(target)}", timeout=30, port=tor_port)
    else:
        log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Searching Ahmia.fi (public .onion index)...")
        resp = robust_http_get(f"https://ahmia.fi/search/?q={requests.utils.quote(target)}",
                               headers={'User-Agent': 'Mozilla/5.0'}, timeout=15, retries=2)
    if resp and resp.status_code == 200:
        try:
            # Result titles
            titles = re.findall(r'<h4[^>]*>\s*(?:<a[^>]*>)?(.*?)(?:</a>)?\s*</h4>', resp.text, re.DOTALL)
            # Onion addresses mentioned anywhere in results (exclude Ahmia's own onion)
            onions = sorted(set(re.findall(r'[a-z2-7]{16,56}\.onion', resp.text)) - {'juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion'})
            for title in titles[:5]:
                clean = re.sub(r'<[^>]+>', '', title).strip()
                if clean and target.lower() in clean.lower():
                    found.append(f"  {Fore.RED}[⚠️]{Fore.WHITE} [Ahmia] {Fore.CYAN}[{target_type}]{Fore.WHITE} -> {Fore.YELLOW}{clean}")
            if onions:
                log_print(f"  {Fore.YELLOW}[ℹ️] {len(onions)} onion service(s) mention this term in the index:")
                for o in onions[:5]:
                    log_print(f"     {Fore.BLUE}http://{o}")
            elif not found:
                log_print(f"  {Fore.GREEN}  [🛡️] No indexed .onion results on Ahmia.")
        except:
            log_print(f"  {Fore.RED}  [❌] Error parsing Ahmia results.")
    else:
        log_print(f"  {Fore.RED}  [❌] Ahmia unreachable.")

    # --- 2. Pastebin-style dumps referenced on dark web gateways ---
    print_progress(2, steps)
    gateways = [
        ("Tor66 (clearnet mirror)", f"https://tor66sewebgixwhcqfnpuxinzhp5yym7opnfvz7im5vq2b6mkzlyqd.onion.pet/search?q={target}"),
    ]
    log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Manual gateway checks (open in Tor Browser if needed):")
    for name, url in gateways:
        log_print(f"     {Fore.BLUE}{url}")

    # --- 3. Breach exposure via public previews (manual, legal) ---
    print_progress(3, steps)
    links = [
        ("Intelligence X (free preview)", f"https://intelx.io/?s={target}"),
        ("BreachDirectory (free view)", f"https://breachdirectory.com/search?term={target}"),
        ("Have I Been Pwned (email)", f"https://haveibeenpwned.com/unifiedsearch/{target}"),
        ("Google Dork: onion mentions", f"https://www.google.com/search?q=%22{target}%22+site:onion.pet+OR+inurl:onion"),
        ("Google Dork: dark web forums", f"https://www.google.com/search?q=%22{target}%22+site:darkwebelite.com+OR+site:dreadforums")
    ]
    log_print(f"  {Fore.CYAN}[🔍]{Fore.WHITE} Breach & dark web exposure previews:")
    for name, url in links:
        log_print(f"     {Fore.BLUE}{url}")

    if found:
        log_print(f"\n{Fore.RED}[!] DARK WEB LEADS FOUND:\n")
        for s in found:
            log_print(s)
    else:
        log_print(f"\n{Fore.GREEN}  [🛡️] No automatic dark web matches (check manual links above).")

# ============================================================
# TOR DETECTION & TOR-ROUTED REQUESTS
# ============================================================

def check_tor_connection():
    """Check if a Tor client is reachable via SOCKS5 (tor daemon: 9050, Tor Browser: 9150)."""
    import socket
    for port in (9050, 9150):
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=3)
            s.close()
            return port
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue
    return None

def tor_get(url, timeout=20, port=9050):
    """HTTP GET routed through the local Tor client (SOCKS5)."""
    proxies = {'http': f'socks5h://127.0.0.1:{port}', 'https': f'socks5h://127.0.0.1:{port}'}
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        return requests.get(url, headers=headers, proxies=proxies, timeout=timeout)
    except Exception:
        return None

# ============================================================
# DEPENDENCY CHECKER (AUTO-INSTALL)
# ============================================================

REQUIRED_PACKAGES = [
    ("requests", "requests"),
    ("colorama", "colorama"),
    ("socks", "pysocks"),
    ("holehe", "holehe"),
]

def check_dependencies(auto=False):
    import importlib.util
    if not auto:
        clear_screen()
        print_dynamic_box([f"{Fore.YELLOW}DEPENDENCY CHECK & AUTO-INSTALL"])

    missing = []
    print(f"\n{Fore.WHITE}Checking installed modules:\n")
    for module, package in REQUIRED_PACKAGES:
        if importlib.util.find_spec(module) is not None:
            print(f"  {Fore.GREEN}[✅]{Fore.WHITE} {module} ({package})")
        else:
            print(f"  {Fore.RED}[❌]{Fore.WHITE} {module} ({package}) {Fore.RED}- missing")
            missing.append(package)

    # Tor status as part of the environment check
    if not auto:
        print(f"\n{Fore.WHITE}Environment:\n")
        tor_port = check_tor_connection()
        if tor_port:
            print(f"  {Fore.GREEN}[✅]{Fore.WHITE} Tor client detected (SOCKS5 127.0.0.1:{tor_port})")
        else:
            print(f"  {Fore.RED}[❌]{Fore.WHITE} Tor client not running (dark web scan will use clearnet mode)")

    if not missing:
        print(f"\n{Fore.GREEN}[+] All dependencies are installed.")
        if not auto:
            input(f"\n{Fore.CYAN}Press Enter to return...")
        return

    print(f"\n{Fore.YELLOW}[ℹ️] {len(missing)} package(s) missing: {', '.join(missing)}")
    if auto:
        confirm = 'y'
    else:
        confirm = input(f"{Fore.YELLOW}[?] Install automatically via pip? (Y/n): {Fore.WHITE}").strip().lower()
    if confirm in ('', 'y', 'yes'):
        for package in missing:
            print(f"\n{Fore.CYAN}[⬇️] Installing {package}...")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    print(f"  {Fore.GREEN}[✅]{Fore.WHITE} {package} installed successfully.")
                else:
                    print(f"  {Fore.RED}[❌]{Fore.WHITE} Failed to install {package}:")
                    print(f"     {Fore.RED}{result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'unknown error'}")
            except Exception as e:
                print(f"  {Fore.RED}[❌]{Fore.WHITE} Error installing {package}: {e}")

        # Re-check after installation
        print(f"\n{Fore.WHITE}Re-checking modules:\n")
        still_missing = []
        for module, package in REQUIRED_PACKAGES:
            if importlib.util.find_spec(module) is not None:
                print(f"  {Fore.GREEN}[✅]{Fore.WHITE} {module} ({package})")
            else:
                print(f"  {Fore.RED}[❌]{Fore.WHITE} {module} ({package}) - still missing")
                still_missing.append(package)
        if still_missing:
            print(f"\n{Fore.YELLOW}[⚠️] Could not install: {', '.join(still_missing)}")
            print(f"{Fore.WHITE}Try manually: pip install {' '.join(still_missing)}")
        else:
            print(f"\n{Fore.GREEN}[+] All dependencies installed successfully.")
    else:
        print(f"{Fore.YELLOW}[ℹ️] Installation skipped.")

    if not auto:
        input(f"\n{Fore.CYAN}Press Enter to return...")

# ============================================================
# REPORT MANAGEMENT
# ============================================================

def manage_reports():
    while True:
        clear_screen()
        menu_lines = [f"{Fore.MAGENTA} MANAGE REPORTS"]
        print_dynamic_box(menu_lines)

        reports = sorted(glob.glob("report_*.txt"))
        if not reports:
            print(f"\n{Fore.YELLOW}  [ℹ️] No reports found.")
            input(f"\n{Fore.CYAN}Press Enter to return...")
            break

        print(f"\n{Fore.WHITE}Found {len(reports)} report(s):\n")
        for i, file in enumerate(reports, 1):
            name = file.replace("report_", "").replace(".txt", "").replace("_", " ")
            print(f"  {Fore.GREEN}{i}.{Fore.WHITE} {name}")

        sub_menu = [
            f"{Fore.YELLOW}1.{Fore.WHITE} View Report",
            f"{Fore.RED}2.{Fore.WHITE} Delete Report",
            f"{Fore.RED}3.{Fore.WHITE} Delete ALL Reports",
            f"{Fore.RED}0.{Fore.WHITE} Back"
        ]
        print()
        print_dynamic_box(sub_menu)

        action = input(f"\n{Fore.YELLOW}👉 Option: {Fore.WHITE}").strip()

        if action in ['1', '2']:
            num = input(f"{Fore.YELLOW}Number: {Fore.WHITE}").strip()
            if num.isdigit() and 1 <= int(num) <= len(reports):
                file = reports[int(num) - 1]
                if action == '1':
                    clear_screen()
                    print_section(f"📄 {file}")
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            print(f"\n{Fore.WHITE}{f.read()}")
                    except:
                        pass
                    input(f"\n{Fore.CYAN}Enter...")
                elif action == '2':
                    if input(f"{Fore.RED}Delete '{file}'? (y/n): {Fore.WHITE}").lower() == 'y':
                        try:
                            os.remove(file)
                            print(f"{Fore.GREEN}[+] Deleted!")
                        except:
                            pass
                    input(f"\n{Fore.CYAN}Enter...")
            else:
                input(f"{Fore.RED}Invalid. Enter...")

        elif action == '3':
            confirm = input(f"{Fore.RED}Delete ALL {len(reports)} reports? (y/n): {Fore.WHITE}").strip().lower()
            if confirm == 'y':
                deleted = 0
                for file in reports:
                    try:
                        os.remove(file)
                        deleted += 1
                    except:
                        pass
                print(f"\n{Fore.GREEN}[+] {deleted} report(s) successfully deleted!")
                input(f"{Fore.CYAN}Enter to continue...")
                break

        elif action == '0':
            break
        else:
            input(f"{Fore.RED}Invalid. Enter...")

# ============================================================
# "ABOUT" SECTION
# ============================================================

def show_about():
    clear_screen()
    about_lines = [
        f"{Fore.YELLOW}ABOUT THE APPLICATION",
        f"",
        f"{Fore.WHITE}OSINT & Threat Intelligence tool",
        f"{Fore.WHITE}focused on digital profiles.",
        f"",
        f"{Fore.WHITE}Investigates emails, usernames,",
        f"{Fore.WHITE}phone numbers, and passwords.",
        f"",
        f"{Fore.WHITE}SEARCH (Standard):",
        f"{Fore.GREEN}-{Fore.WHITE} Auto-updating 300+ sites (Sherlock)",
        f"{Fore.GREEN}-{Fore.WHITE} Email: Holehe, Gravatar, EmailRep",
        f"{Fore.GREEN}-{Fore.WHITE} User: Namechk, Wayback Machine",
        f"{Fore.GREEN}-{Fore.WHITE} Phone: WhatsApp, Truecaller, Dorks",
        f"{Fore.GREEN}-{Fore.WHITE} Leaks: Pastebin, GitHub (public only)",
        f"{Fore.GREEN}-{Fore.WHITE} Passwords: HIBP, Dorks",
        f"",
        f"{Fore.WHITE}ANALYSIS MODULES:",
        f"{Fore.GREEN}-{Fore.WHITE} Fake Profile Scanner (heuristics)",
        f"{Fore.GREEN}-{Fore.WHITE} Entropy analysis (bot accounts)",
        f"{Fore.GREEN}-{Fore.WHITE} Dark Web Scan (Ahmia, legal sources)",
        f"{Fore.GREEN}-{Fore.WHITE} Domains: crt.sh subdomain search",
        f"",
        f"{Fore.WHITE}ADVANCED SCAN (automatic):",
        f"{Fore.GREEN}-{Fore.WHITE} Detects Tor client (SOCKS5:9050)",
        f"{Fore.GREEN}-{Fore.WHITE} Tor ON: scans .onion services",
        f"{Fore.GREEN}-{Fore.WHITE} Tor OFF: clearnet mode + noted in report",
        f"",
        f"{Fore.GREEN}-{Fore.WHITE} Auto-saves & manages .txt reports",
        f"",
        f"{Fore.WHITE}Open Source and Free.",
        f"",
        f"{Fore.CYAN}GitHub:",
        f"{Fore.BLUE}https://github.com/seu-usuario/",
    ]
    print_dynamic_box(about_lines)
    input(f"\n{Fore.CYAN}Press Enter to return...")

# ============================================================
# MAIN FUNCTION
# ============================================================

def save_report(target):
    global report_buffer
    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    safe = re.sub(r'[^a-zA-Z0-9.@_-]', '', target)
    filename = f"report_{safe}_{date}.txt"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"--- OSINT Report: {target} ---\n")
            f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for l in report_buffer:
                f.write(l + "\n")
        log_print(f"\n{Fore.GREEN}[+] Report: {filename}")
    except Exception as e:
        print(f"{Fore.RED}[!] Failed to save report: {e}")
    report_buffer = []

def investigate_all(target):
    global report_buffer
    report_buffer = []
    clear_screen()

    tor_port = check_tor_connection()

    if target.startswith("http://"):
        target = target[7:]
    if target.startswith("https://"):
        target = target[8:]
    target = target.split('/')[0]

    print_section("🔌 TOR CLIENT STATUS")
    if tor_port:
        log_print(f"  {Fore.GREEN}[✅] Tor Browser/client: {Fore.GREEN}CONNECTED{Fore.WHITE} (SOCKS5 127.0.0.1:{tor_port})")
        log_print(f"  {Fore.WHITE}Advanced dark web scan {Fore.GREEN}enabled{Fore.WHITE}.")
    else:
        log_print(f"  {Fore.RED}[❌] Tor Browser/client: {Fore.RED}DISCONNECTED{Fore.WHITE}")
        log_print(f"  {Fore.YELLOW}[⚠️] Dark web scan running in limited clearnet mode.")

    if is_email(target):
        investigate_email(target)
        target_type = "Email"
    elif is_domain(target):
        investigate_domain(target)
        target_type = "Domain"
    elif is_phone(target):
        investigate_phone(target)
        target_type = "Phone"
    else:
        investigate_username(target)
        target_type = "Username/Password"

    investigate_leaks(target, target_type)
    fake_profile_scanner(target, target_type)
    dark_web_scan(target, target_type, tor_port=tor_port)

    print_dynamic_box([f"{Fore.MAGENTA} Analysis Complete."])
    save_report(target)

# ============================================================
# MENU
# ============================================================

def main():
    clear_screen()
    print_dynamic_box([f"{Fore.YELLOW}OSINT THREAT INTELLIGENCE"])
    print(f"\n{Fore.CYAN}Initialising environment...")

    # Auto-check and install missing dependencies (no user input)
    check_dependencies(auto=True)

    # Auto-update platform database
    watchdog_platforms()

    tor_port = check_tor_connection()
    if tor_port:
        print(f"{Fore.GREEN}[✅] Tor client detected (port {tor_port}).")
    else:
        print(f"{Fore.YELLOW}[ℹ️] Tor client not running (clearnet mode).")

    print(f"\n{Fore.GREEN}[✅] Application running correctly.\n")
    time.sleep(2)

    while True:
        clear_screen()
        menu_lines = [
            f"{Fore.YELLOW}OSINT THREAT INTELLIGENCE",
            f"",
            f"{Fore.GREEN}1.{Fore.WHITE} Search (Email/User/Phone/Pass)",
            f"{Fore.BLUE}2.{Fore.WHITE} Manage Reports",
            f"{Fore.MAGENTA}3.{Fore.WHITE} About",
            f"{Fore.RED}0.{Fore.WHITE} Exit",
        ]
        print_dynamic_box(menu_lines)

        choice = input(f"\n{Fore.YELLOW}👉 Option: {Fore.WHITE}").strip()
        if choice == '1':
            target = input(f"{Fore.YELLOW}🔍 Target: {Fore.WHITE}").strip()
            if target:
                try:
                    investigate_all(target)
                except KeyboardInterrupt:
                    print(f"{Fore.RED}\n[!] Investigation interrupted by user.")
                except Exception as e:
                    print(f"{Fore.RED}[!] Unexpected error during investigation: {e}")
            input(f"\n{Fore.CYAN}Enter...")
        elif choice == '2':
            manage_reports()
        elif choice == '3':
            show_about()
        elif choice == '0':
            clear_screen()
            print_dynamic_box([f"{Fore.YELLOW} Exiting... "])
            print()
            break
        else:
            input(f"{Fore.RED}Invalid. Enter...")

if __name__ == "__main__":
    main()
EOF

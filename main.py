import time
import random
import logging
import sys
import re
import hashlib
import threading
import requests
from pathlib import Path
from camoufox.sync_api import Camoufox

from config import CONFIG

_file_lock = threading.Lock()
_success_count = 0
_counter_lock = threading.Lock()

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))

root_logger.handlers = [console_handler]

logger = logging.getLogger(__name__)


FIRST_NAMES = [
    'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda',
    'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica',
    'Thomas', 'Sarah', 'Charles', 'Karen', 'Christopher', 'Nancy', 'Daniel', 'Margaret',
    'Matthew', 'Lisa', 'Anthony', 'Betty', 'Mark', 'Sandra', 'Donald', 'Ashley',
    'Steven', 'Kimberly', 'Paul', 'Emily', 'Andrew', 'Donna', 'Joshua', 'Michelle',
    'Kenneth', 'Carol', 'Kevin', 'Amanda', 'Brian', 'Dorothy', 'George', 'Melissa',
    'Edward', 'Deborah', 'Ronald', 'Stephanie', 'Timothy', 'Rebecca', 'Jason', 'Sharon',
    'Jeffrey', 'Laura', 'Ryan', 'Cynthia', 'Jacob', 'Kathleen', 'Gary', 'Amy',
    'Nicholas', 'Shirley', 'Eric', 'Angela', 'Jonathan', 'Helen', 'Stephen', 'Anna',
    'Larry', 'Brenda', 'Justin', 'Pamela', 'Scott', 'Nicole', 'Brandon', 'Emma',
    'Benjamin', 'Samantha', 'Samuel', 'Katherine', 'Gregory', 'Christine', 'Frank', 'Debra',
    'Alexander', 'Rachel', 'Raymond', 'Catherine', 'Patrick', 'Carolyn', 'Jack', 'Janet',
    'Dennis', 'Ruth', 'Jerry', 'Maria', 'Tyler', 'Heather', 'Aaron', 'Diane',
    'Henry', 'Virginia', 'Douglas', 'Julie', 'Jose', 'Joyce', 'Peter', 'Victoria',
    'Adam', 'Olivia', 'Nathan', 'Kelly', 'Zachary', 'Christina', 'Walter', 'Lauren',
    'Kyle', 'Joan', 'Harold', 'Evelyn', 'Carl', 'Judith', 'Arthur', 'Andrea',
    'Gerald', 'Hannah', 'Roger', 'Megan', 'Keith', 'Cheryl', 'Jeremy', 'Jacqueline',
    'Terry', 'Martha', 'Lawrence', 'Gloria', 'Sean', 'Teresa', 'Christian', 'Ann',
    'Ethan', 'Sara', 'Austin', 'Madison', 'Joe', 'Frances', 'Albert', 'Kathryn',
    'Jesse', 'Janice', 'Willie', 'Jean', 'Billy', 'Abigail', 'Bryan', 'Alice',
    'Bruce', 'Judy', 'Jordan', 'Sophia', 'Dylan', 'Grace', 'Noah', 'Denise',
    'Alan', 'Amber', 'Ralph', 'Doris', 'Gabriel', 'Marilyn', 'Logan', 'Danielle',
    'Wayne', 'Beverly', 'Vincent', 'Isabella', 'Eugene', 'Theresa', 'Randy', 'Diana',
    'Harry', 'Natalie', 'Philip', 'Brittany', 'Louis', 'Charlotte', 'Bobby', 'Marie',
    'Johnny', 'Kayla', 'Mason', 'Alexis', 'Eduardo', 'Lori',
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
    'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
    'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
    'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
    'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill',
    'Flores', 'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell',
    'Mitchell', 'Carter', 'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz',
    'Parker', 'Cruz', 'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales',
    'Murphy', 'Cook', 'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson',
    'Bailey', 'Reed', 'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward',
    'Richardson', 'Watson', 'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray',
    'Mendoza', 'Ruiz', 'Hughes', 'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel',
    'Myers', 'Long', 'Ross', 'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry',
    'Russell', 'Sullivan', 'Bell', 'Coleman', 'Butler', 'Henderson', 'Barnes', 'Gonzales',
    'Fisher', 'Vasquez', 'Simmons', 'Romero', 'Jordan', 'Patterson', 'Alexander', 'Hamilton',
    'Graham', 'Reynolds', 'Griffin', 'Wallace', 'Moreno', 'West', 'Cole', 'Hayes',
    'Bryant', 'Herrera', 'Gibson', 'Ellis', 'Tran', 'Medina', 'Aguilar', 'Stevens',
    'Murray', 'Ford', 'Castro', 'Marshall', 'Owens', 'Harrison', 'Fernandez', 'Mcdonald',
    'Woods', 'Washington', 'Kennedy', 'Wells', 'Vargas', 'Henry', 'Chen', 'Freeman',
    'Webb', 'Tucker', 'Guzman', 'Burns', 'Crawford', 'Olson', 'Simpson', 'Porter',
    'Hunter', 'Gordon', 'Mendez', 'Silva', 'Shaw', 'Snyder', 'Mills', 'Pearson',
]


def generate_human_name() -> str:
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return f"{first} {last}"


JUNK_RESOURCES = [
    'fonts.gstatic.com',
    'fonts.googleapis.com',
    'google-analytics.com',
    'googletagmanager.com',
    'googleadservices.com',
    'doubleclick.net',
    'facebook.net',
    '.fbcdn.net',
    'mc.yandex',
    'hotjar.com',
    'clarity.ms',
    'mixpanel',
    'sentry.io',
    'play.google.com/log',
    'static.onecompiler.com/images/',
]

IMG_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.ico')


def _route_handler(route):
    url = route.request.url.lower()
    if any(j in url for j in JUNK_RESOURCES) or url.split('?')[0].endswith(IMG_EXTS):
        route.abort()
    else:
        route.continue_()


class Worker:

    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.lock = threading.RLock()
        self._fox = None
        self.browser = None
        self._owner_tid = None

    def _check_thread(self):
        tid = threading.get_ident()
        if self._owner_tid is not None and self._owner_tid != tid:
            raise RuntimeError(
                f"Worker {self.worker_id}: Camoufox browser is locked to thread "
                f"{self._owner_tid} but accessed from thread {tid}. "
                "Each worker thread must own its own browser."
            )

    def ensure_browser(self):
        with self.lock:
            self._check_thread()
            if self.browser is None:
                logger.info(f"[w{self.worker_id}] launching browser...")
                self._owner_tid = threading.get_ident()
                self._fox = Camoufox(
                    i_know_what_im_doing=True,
                    disable_coop=True,
                    headless=CONFIG.get('headless', False),
                    window=(CONFIG['viewport_width'], CONFIG['viewport_height']),
                )
                self.browser = self._fox.__enter__()
            return self.browser

    def close(self):
        with self.lock:
            if self._fox is not None:
                try:
                    self._fox.__exit__(None, None, None)
                except Exception:
                    pass
                self.browser = None
                self._fox = None


def _click_safe(page, selector, evaluate_fn=None):
    try:
        loc = page.locator(selector)
        if loc.count() > 0 and loc.first.is_visible():
            loc.first.click(force=True, timeout=5000)
            return True
    except Exception:
        pass
    try:
        if evaluate_fn:
            page.evaluate(evaluate_fn)
            return True
    except Exception:
        pass
    return False


def extract_token(page) -> str:
    try:
        token = page.evaluate("""
            () => {
                try {
                    const raw = localStorage.getItem('reduxState');
                    if (raw) {
                        const state = JSON.parse(raw);
                        const user = state.userLogin || state.user || state.auth;
                        if (user && user.token) return user.token;
                        if (user && user.accessToken) return user.accessToken;
                    }
                } catch(e) {}
                const keys = ['token', 'access_token', 'auth_token', 'jwt', 'accessToken'];
                for (const key of keys) {
                    let val = localStorage.getItem(key);
                    if (val && val.length > 50) return val;
                    val = sessionStorage.getItem(key);
                    if (val && val.length > 50) return val;
                }
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    const val = localStorage.getItem(key);
                    if (val && val.length > 80 && val.split('.').length === 3) return val;
                }
                const cookies = document.cookie.split(';');
                for (const c of cookies) {
                    const [name, ...rest] = c.trim().split('=');
                    if (name === 'token' || name === 'auth_token') {
                        const val = rest.join('=');
                        if (val && val.length > 50) return val;
                    }
                }
                return null;
            }
        """)
        if token and len(token) > 20:
            return token
    except Exception:
        pass
    return None


OTP_PATTERN = re.compile(
    r'(?:one[- ]time[- ]password|otp|verification code|activate code|activation code|'
    r'security code|validation code|confirm code|code)[^0-9]{0,8}(\d{4,8})',
    re.IGNORECASE,
)

OTP_CONTEXT = re.compile(
    r'(?:\bOTP\b|password|code|verif|authoriz|secur|confirm|activ|one[- ]time)',
    re.IGNORECASE,
)


def _extract_otp(combined):
    m = OTP_PATTERN.search(combined)
    if m:
        return m.group(1)
    subject = (combined.split('\n', 1)[0] or '').strip()
    if OTP_CONTEXT.search(subject):
        m = re.search(r'\b(\d{6})\b', combined)
        if m:
            return m.group(1)
        m = re.search(r'\b(\d{4})\b', combined)
        if m:
            return m.group(1)
    return None


class TempMailBase:

    name = 'base'
    PASSWORD = 'Passw0rd!123'

    def __init__(self):
        self.email = None
        self.token = None
        self.ready = threading.Event()
        self.session = requests.Session()
        self._seen_log = set()
        self.rate_limited = False
        self.retry_after = 0

    def _log_new_email(self, msg_id, message=None):
        if msg_id in self._seen_log:
            return
        self._seen_log.add(msg_id)
        if message:
            logger.info(message)

    def create_account(self):
        raise NotImplementedError

    def fetch_messages(self):
        raise NotImplementedError

    def get_otp(self, timeout=90):
        start_time = time.time()
        seen_ids = set()
        poll = getattr(self, 'poll_interval', 3)
        while time.time() - start_time < timeout:
            try:
                messages = self.fetch_messages()
            except Exception:
                time.sleep(poll)
                continue

            for msg_id, text_content, html_content in messages:
                if not msg_id or msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                combined = (text_content or '') + ' ' + (html_content or '')

                otp = _extract_otp(combined)
                if otp:
                    return otp

            time.sleep(poll)

        logger.warning(f"Timeout waiting for OTP email ({self.name})")
        return None


class TempMailLol(TempMailBase):
    # https://tempmail.lol/en/api (API v2, free tier - no API key required)
    name = 'tempmail.lol'
    BASE = 'https://api.tempmail.lol/v2'

    def create_account(self):
        headers = {
            'User-Agent': 'TempMailPythonAPI/3.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        for attempt in range(5):
            try:
                resp = self.session.post(
                    f'{self.BASE}/inbox/create',
                    json={},
                    headers=headers,
                    timeout=20,
                )
                if resp.status_code == 429:
                    self.rate_limited = True
                    try:
                        self.retry_after = float(resp.headers.get('Retry-After', 0)) or 60
                    except Exception:
                        self.retry_after = 60
                    logger.warning("tempmail.lol rate limited, failing over to next provider...")
                    return False
                if resp.status_code not in (200, 201):
                    logger.warning(f"tempmail.lol offline (/inbox/create {resp.status_code}), skipping")
                    return False
                try:
                    data = resp.json()
                except Exception:
                    return False
                self.email = data.get('address')
                self.token = data.get('token')
                if self.email and self.token:
                    self.ready.set()
                    logger.info(f"Created tempmail.lol inbox: {self.email}")
                    return True
            except Exception as e:
                logger.error(f"Error creating tempmail.lol inbox: {e}")
                return False
            time.sleep(1.5)
        return False

    def fetch_messages(self):
        if not self.token:
            return []
        try:
            resp = self.session.get(
                f'{self.BASE}/inbox',
                params={'token': self.token},
                headers={
                    'User-Agent': 'TempMailPythonAPI/3.0',
                    'Accept': 'application/json',
                },
                timeout=20,
            )
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        if not isinstance(data, dict):
            return []
        if data.get('expired'):
            return []
        emails = data.get('emails') or []
        if not isinstance(emails, list):
            return []

        out = []
        for em in emails:
            if not isinstance(em, dict):
                continue
            sender = em.get('from', '') or ''
            recipient = em.get('to', '') or ''
            subject = em.get('subject', '') or ''
            body = em.get('body', '') or ''
            html = em.get('html', '') or ''
            date = str(em.get('date', '') or '')
            # API v2 emails carry no id, synthesize a stable one
            msg_id = hashlib.sha1(
                f"{sender}|{recipient}|{subject}|{body}|{date}".encode('utf-8', 'ignore')
            ).hexdigest()
            if subject or sender:
                self._log_new_email(msg_id, f"  New email: subject='{subject}' from='{sender}'")
            text_content = subject + '\n' + body
            html_content = html if isinstance(html, str) else ''
            out.append((msg_id, text_content, html_content))
        return out


class TempTf(TempMailBase):
    # https://temp.tf/document - no API key required, 60 req/min per IP
    name = 'temp.tf'
    BASE = 'https://temp.tf/api'
    poll_interval = 5

    def create_account(self):
        for attempt in range(5):
            try:
                resp = self.session.get(
                    f'{self.BASE}/account',
                    params={'dot': 1, 'plus': 1},
                    headers={
                        'User-Agent': 'Mozilla/5.0',
                        'Accept': 'application/json',
                    },
                    timeout=20,
                )
                if resp.status_code == 429:
                    self.rate_limited = True
                    try:
                        self.retry_after = float(resp.headers.get('Retry-After', 0)) or 60
                    except Exception:
                        self.retry_after = 60
                    logger.warning("temp.tf rate limited, failing over to next provider...")
                    return False
                if resp.status_code != 200:
                    logger.warning(f"temp.tf offline (GET /account {resp.status_code}), skipping")
                    return False
                try:
                    email = resp.json().get('email')
                except Exception:
                    return False
                if email:
                    self.email = email
                    self.token = email  # /check authenticates with the address itself
                    self.ready.set()
                    logger.info(f"Created temp.tf inbox: {self.email}")
                    return True
            except Exception as e:
                logger.error(f"Error creating temp.tf inbox: {e}")
                return False
            time.sleep(1.5)
        return False

    def fetch_messages(self):
        if not self.email:
            return []
        try:
            resp = self.session.post(
                f'{self.BASE}/check',
                json={'email': self.email},
                headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
                timeout=20,
            )
        except Exception:
            return []
        if resp.status_code != 200:
            return []
        try:
            data = resp.json()
        except Exception:
            return []
        if not isinstance(data, dict):
            return []
        messages = data.get('data') or []
        if not isinstance(messages, list):
            return []

        out = []
        for em in messages:
            if not isinstance(em, dict):
                continue
            subject = em.get('subject', '') or ''
            sender = em.get('from', '') or ''
            body = em.get('body', '') or ''
            date = str(em.get('date', '') or '')
            msg_id = f"{em.get('id', '')}|{date}|{subject}"
            if subject or sender:
                self._log_new_email(msg_id, f"  New email: subject='{subject}' from='{sender}'")
            if em.get('bodyContentType') == 'html':
                html_content = body if isinstance(body, str) else ''
                text_content = subject + '\n' + re.sub(r'<[^>]+>', ' ', html_content)
            else:
                text_content = subject + '\n' + (body if isinstance(body, str) else '')
                html_content = ''
            out.append((msg_id, text_content, html_content))
        return out


PROVIDERS = [TempMailLol, TempTf]

_provider_rotate_lock = threading.Lock()
_provider_rotate = 0
_provider_cooldown_lock = threading.Lock()
_provider_cooldown = {}  # provider name -> unix timestamp until which it is skipped


def _create_temp_mail():
    global _provider_rotate

    with _provider_rotate_lock:
        start = _provider_rotate % len(PROVIDERS)
        _provider_rotate += 1

    order = [PROVIDERS[(start + i) % len(PROVIDERS)] for i in range(len(PROVIDERS))]
    now = time.time()
    with _provider_cooldown_lock:
        available = [cls for cls in order if _provider_cooldown.get(cls.name, 0) <= now]
    if not available:
        with _provider_cooldown_lock:
            earliest = min(_provider_cooldown.get(cls.name, 0) for cls in order)
        wait = max(0, earliest - time.time())
        if wait > 0:
            logger.warning(f"All temp-mail providers rate limited, waiting {wait:.0f}s...")
            time.sleep(wait)
        available = order

    for provider_cls in available:
        provider = provider_cls()
        thread = threading.Thread(target=provider.create_account, daemon=True)
        thread.start()
        deadline = time.time() + 50
        while not provider.ready.is_set():
            if not thread.is_alive():
                break
            if time.time() > deadline:
                break
            time.sleep(0.5)
        if provider.ready.is_set():
            return provider
        if getattr(provider, 'rate_limited', False):
            until = time.time() + (provider.retry_after or 60)
            with _provider_cooldown_lock:
                _provider_cooldown[provider.name] = until
            logger.warning(f"Temp-mail provider {provider.name} rate limited, cooling down...")
        else:
            logger.warning(f"Temp-mail provider {provider.name} failed, trying next...")
    return None


def _captcha_token_present(page):
    try:
        return page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input');
                for (const inp of inputs) {
                    const n = (inp.name || '').toLowerCase();
                    if ((n.includes('captcha') || n.includes('turnstile') || (n.includes('recaptcha') ) ) && inp.value && inp.value.length > 10) return true;
                }
                try { const r = window.grecaptcha && window.grecaptcha.getResponse && window.grecaptcha.getResponse(); if (r && r.length > 10) return true; } catch(e) {}
                try { const r = window.turnstile && window.turnstile.getResponse && window.turnstile.getResponse(); if (r && r.length > 10) return true; } catch(e) {}
                return false;
            }
        """)
    except Exception:
        return False


def _wait_for_captcha(page, timeout=None):
    timeout = timeout or CONFIG.get('turnstile_timeout', 12)
    start = time.time()
    clicked = False
    clicked_at = 0
    while time.time() - start < timeout:
        if _captcha_token_present(page):
            return True

        if clicked and time.time() - clicked_at > 5:
            clicked = False

        if not clicked:
            try:
                for frame in page.frames:
                    if 'challenges.cloudflare.com' in (frame.url or ''):
                        checkbox = frame.locator('input[type="checkbox"], label, .cb-lb, #challenge-stage')
                        if checkbox.count() > 0 and checkbox.first.is_visible():
                            checkbox.first.click()
                            clicked = True
                            clicked_at = time.time()
                            time.sleep(2)
                            break
                        body = frame.locator('body')
                        if body.count() > 0:
                            body.first.click(position={'x': 25, 'y': 35})
                            clicked = True
                            clicked_at = time.time()
                            time.sleep(2)
                            break
            except Exception:
                pass

        time.sleep(1)

    return False


def _gen_password():
    pw_chars = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    pw = [random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), random.choice('0123456789')] + random.choices(pw_chars, k=14)
    random.shuffle(pw)
    return ''.join(pw)


def signup(browser, password, mail):
    context = browser.new_context(
        viewport={'width': CONFIG['viewport_width'], 'height': CONFIG['viewport_height']}
    )
    context.route('**/*', _route_handler)
    page = context.new_page()

    try:
        page.goto('https://onecompiler.com/chat', timeout=CONFIG['timeout'])
        try:
            page.wait_for_selector('button, a, input', timeout=30000)
        except Exception:
            pass

        page.bring_to_front()

        login_clicked = False
        for sel in ['button[aria-label="Login"]', 'button:has-text("Login")', 'button:has-text("Log in")', 'a:has-text("Login")', 'a:has-text("Log in")']:
            if _click_safe(page, sel):
                login_clicked = True
                break
        if not login_clicked:
            login_clicked = page.evaluate("""
                () => {
                    const buttons = document.querySelectorAll('button, a');
                    for (const btn of buttons) {
                        const t = (btn.textContent || '').trim().toLowerCase();
                        const l = (btn.getAttribute('aria-label') || '').toLowerCase();
                        if (t === 'login' || t === 'log in' || l === 'login' || l === 'log in') { btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); return true; }
                    }
                    return false;
                }
            """)

        try:
            page.wait_for_selector('button:has-text("Sign Up"), a:has-text("Sign Up"), button:has-text("Sign up"), a:has-text("Sign up"), button:has-text("New to OneCompiler"), a:has-text("New to OneCompiler")', timeout=15000)
        except Exception:
            pass

        signup_clicked = False
        for sel in ['button:has-text("Sign Up")', 'button:has-text("Sign up")', 'a:has-text("Sign Up")', 'a:has-text("Sign up")', 'button:has-text("New to OneCompiler")', 'a:has-text("New to OneCompiler")']:
            if _click_safe(page, sel):
                signup_clicked = True
                break
        if not signup_clicked:
            signup_clicked = page.evaluate("""
                () => {
                    const els = document.querySelectorAll('button, a');
                    for (const el of els) {
                        const t = (el.textContent || '').trim().toLowerCase();
                        if (t.includes('sign up') || t.includes('new to onecompiler') || t.includes('create new account')) { el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); return true; }
                    }
                    return false;
                }
            """)

        try:
            page.wait_for_selector('input[id="name"], input[placeholder*="name" i]', timeout=15000)
        except Exception:
            pass

        name = generate_human_name()
        name_filled = False
        for sel in ['input[id="name"]', 'input[placeholder*="name" i]']:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.fill(name)
                name_filled = True
                break
        if not name_filled:
            inputs = page.locator('input')
            for i in range(inputs.count()):
                ph = inputs.nth(i).get_attribute('placeholder') or ''
                if 'name' in ph.lower():
                    inputs.nth(i).fill(name)
                    name_filled = True
                    break
        if not name_filled:
            logger.error("Could not find name input")
            return None

        if not mail or not mail.email or not mail.token:
            logger.error("Temp email not ready")
            return None
        email = mail.email

        email_filled = False
        for sel in ['input[id="email"]', 'input[type="email"]', 'input[placeholder*="email" i]']:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.fill(email)
                email_filled = True
                break
        if not email_filled:
            logger.error("Could not find email input")
            return None

        pw_filled = False
        for sel in ['input[id="password"]', 'input[type="password"]', 'input[placeholder*="password" i]']:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.fill(password)
                pw_filled = True
                break
        if not pw_filled:
            logger.error("Could not find password input")
            return None

        captcha_ok = _wait_for_captcha(page)
        if not captcha_ok:
            logger.warning("Captcha unsolved, submitting anyway...")

        submit_clicked = False
        for sel in ['button:has-text("Sign Up"):not([disabled])', 'button:has-text("Sign up"):not([disabled])']:
            if _click_safe(page, sel):
                submit_clicked = True
                break
        if not submit_clicked:
            submit_clicked = page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button');
                    for (const btn of btns) {
                        if (!btn.disabled && (btn.textContent || '').trim().toLowerCase().includes('sign up')) { btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); return true; }
                    }
                    return false;
                }
            """)
        if not submit_clicked:
            logger.error("No submit button found")
            return None

        try:
            page.wait_for_selector('input[id="otp"], input[placeholder*="OTP" i], input[placeholder*="otp" i]', timeout=15000)
        except Exception:
            pass
        otp_field_visible = page.evaluate("() => !!document.querySelector('input[id=\"otp\"], input[placeholder*=\"OTP\" i], input[placeholder*=\"otp\" i]')")
        if not otp_field_visible:
            logger.error("OTP field never appeared")
            return None

        otp = mail.get_otp(timeout=CONFIG.get('otp_timeout', 90))
        if not otp:
            logger.error("No OTP received")
            return None
        logger.info(f"OTP: {otp}")

        otp_filled = False
        for sel in ['input[id="otp"]', 'input[placeholder*="OTP" i]']:
            loc = page.locator(sel)
            if loc.count() > 0 and loc.first.is_visible():
                loc.first.fill(otp)
                otp_filled = True
                break
        if not otp_filled:
            logger.error("Could not find OTP input")
            return None

        _wait_for_captcha(page)

        finish_clicked = False
        for sel in ['button:has-text("Finish Sign Up")', 'button:has-text("Finish sign up")', 'button:has-text("Verify")', 'button:has-text("Confirm")']:
            if _click_safe(page, sel):
                finish_clicked = True
                break
        if not finish_clicked:
            finish_clicked = page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button');
                    for (const btn of btns) {
                        const t = (btn.textContent || '').trim().toLowerCase();
                        if (t.includes('finish sign up') || t.includes('verify') || t.includes('confirm')) { btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window})); return true; }
                    }
                    return false;
                }
            """)
        if not finish_clicked:
            logger.error("No finish button found")
            return None

        try:
            page.wait_for_url('**/chat**', timeout=10000)
        except Exception:
            pass

        deadline = time.time() + 15
        stored_token = None
        while time.time() < deadline:
            stored_token = extract_token(page)
            if stored_token and len(stored_token) > 20:
                break
            time.sleep(1)

        if stored_token and len(stored_token) > 20:
            logger.info(f"Token: {stored_token[:50]}...")
            return stored_token

        logger.warning(f"No token found (URL: {page.url})")
        return None

    except Exception as e:
        logger.error(f"Error: {e}")
        return None
    finally:
        try:
            context.close()
        except Exception:
            pass


def _write_account(email, password, token=None):
    with _file_lock:
        with open('output/accounts.txt', 'a') as f:
            f.write(f"{email}:{password}\n")
        if token:
            with open('output/tokens.txt', 'a') as f:
                f.write(f"{token}\n")


def _create_account(worker):
    global _success_count
    with worker.lock:
        password = _gen_password()
        mail = _create_temp_mail()
        if not mail:
            logger.error("All temp-mail providers failed")
            return None

        browser = worker.ensure_browser()

        result = signup(browser, password, mail)

        if result:
            email = mail.email
            token = result if isinstance(result, str) else "SUCCESS"
            with _counter_lock:
                _success_count += 1
            _write_account(email, password, token)


def _worker_loop(worker, remaining):
    recycle_after = CONFIG.get('browser_recycle_after', 50)
    accounts_since_recycle = 0
    try:
        for _ in range(remaining):
            try:
                _create_account(worker)
            except Exception as e:
                logger.error(f"Worker {worker.worker_id} crashed: {e}")
            time.sleep(1 + random.uniform(0, 1.5))

            accounts_since_recycle += 1
            if accounts_since_recycle >= recycle_after:
                logger.info(f"[w{worker.worker_id}] recycling browser after {accounts_since_recycle} accounts...")
                try:
                    worker.close()
                except Exception:
                    pass
                accounts_since_recycle = 0
    finally:
        worker.close()


def main():
    global _success_count

    count = CONFIG.get('count', 1)
    threads = max(1, min(CONFIG.get('threads', 1), count))

    print(f"\nOneCompiler Account Generator | {count} accounts, {threads} thread(s)")

    _success_count = 0
    Path('output').mkdir(exist_ok=True)

    workers = [Worker(i) for i in range(threads)]
    base, extra = divmod(count, threads)
    schedules = [base + (1 if i < extra else 0) for i in range(threads)]

    runner_threads = []
    for worker, remaining in zip(workers, schedules):
        if remaining <= 0:
            continue
        t = threading.Thread(target=_worker_loop, args=(worker, remaining), daemon=True)
        runner_threads.append(t)
        t.start()

    for t in runner_threads:
        t.join()

    print(f"\n{_success_count} accounts created successfully")
    print(f"Output: output/accounts.txt | output/tokens.txt")


if __name__ == "__main__":
    main()
import time
import random
import logging
import sys
import re
import threading
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
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


class TempEmail:

    BASE = 'https://api.mail.tm'

    def __init__(self):
        self.email = None
        self.password = 'Passw0rd!123'
        self.session = requests.Session()
        self.token = None

    def create_account(self):
        for attempt in range(5):
            try:
                resp = self.session.get(f'{self.BASE}/domains')
                if resp.status_code == 429:
                    time.sleep(3 + attempt * 3 + random.uniform(0, 2))
                    continue
                if resp.status_code != 200:
                    time.sleep(2)
                    continue
                domains = resp.json().get('hydra:member', [])
                if not domains:
                    time.sleep(2)
                    continue
                domain = domains[0]['domain']

                addr = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12))
                self.email = f'{addr}@{domain}'

                resp = self.session.post(f'{self.BASE}/accounts', json={
                    'address': self.email,
                    'password': self.password,
                })
                if resp.status_code in [200, 201]:
                    return self._login()
                elif resp.status_code == 422:
                    return self._login()
                elif resp.status_code == 429:
                    time.sleep(5 + attempt * 3 + random.uniform(0, 3))
                    continue
                else:
                    return False
            except Exception:
                return False
        return False

    def _login(self):
        try:
            resp = self.session.post(f'{self.BASE}/token', json={
                'address': self.email,
                'password': self.password,
            })
            if resp.status_code in [200, 201]:
                self.token = resp.json().get('token')
                if self.token:
                    self.session.headers['Authorization'] = f'Bearer {self.token}'
                    return True
            return False
        except Exception:
            return False

    def get_otp(self, timeout=90):
        start_time = time.time()
        seen_ids = set()
        poll_count = 0
        while time.time() - start_time < timeout:
            poll_count += 1
            try:
                resp = self.session.get(f'{self.BASE}/messages')
                if resp.status_code != 200:
                    time.sleep(3)
                    continue

                data = resp.json()
                messages = data.get('hydra:member', []) if isinstance(data, dict) else data
            except Exception:
                time.sleep(3)
                continue

            if not messages:
                time.sleep(3)
                continue

            for msg_summary in messages:
                msg_id = msg_summary.get('id', '')
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                try:
                    msg_resp = self.session.get(f'{self.BASE}/messages/{msg_id}')
                    if msg_resp.status_code != 200:
                        continue
                    full_msg = msg_resp.json()
                except Exception:
                    continue

                text_content = full_msg.get('text', '') or full_msg.get('body', '') or ''
                html_content = full_msg.get('html', [])
                if isinstance(html_content, list):
                    html_content = ' '.join(html_content)

                combined = text_content + ' ' + html_content

                otp_match = re.search(r'(?:OTP|verification code|code)[:\s]*(\d{4,8})', combined, re.IGNORECASE)
                if otp_match:
                    return otp_match.group(1)

                otp_match = re.search(r'\b(\d{6})\b', combined)
                if otp_match:
                    return otp_match.group(1)

                otp_match = re.search(r'\b(\d{4})\b', combined)
                if otp_match:
                    return otp_match.group(1)

            time.sleep(3)

        logger.warning("Timeout waiting for OTP email")
        return None


def _wait_for_turnstile(page, timeout=30):
    start = time.time()
    clicked = False
    clicked_at = 0
    while time.time() - start < timeout:
        try:
            solved = page.evaluate("""
                () => {
                    const input = document.querySelector('input[name="cf-turnstile-response"]');
                    return !!(input && input.value && input.value.length > 10);
                }
            """)
            if solved:
                return True
        except Exception:
            pass

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

        if not clicked:
            try:
                iframe_box = page.evaluate("""
                    () => {
                        const iframes = document.querySelectorAll('iframe');
                        for (const iframe of iframes) {
                            const rect = iframe.getBoundingClientRect();
                            if (rect.width > 50 && rect.height > 20) {
                                return {x: rect.x, y: rect.y, w: rect.width, h: rect.height};
                            }
                        }
                        return null;
                    }
                """)
                if iframe_box:
                    page.mouse.click(iframe_box['x'] + 25, iframe_box['y'] + iframe_box['h'] - 15)
                    clicked = True
                    clicked_at = time.time()
                    time.sleep(2)
            except Exception:
                pass

        time.sleep(1)

    return False


def signup(email, password, mail=None):
    logger.info(f"Starting signup: {email}")

    try:
        with Camoufox(
            i_know_what_im_doing=True,
            disable_coop=True,
            window=(CONFIG['viewport_width'], CONFIG['viewport_height']),
        ) as browser:
            page = browser.new_page()

            try:
                page.goto('https://onecompiler.com/chat', timeout=CONFIG['timeout'])
                time.sleep(5)
                page.wait_for_selector('button, a, input', timeout=30000)

                # Click Login button
                login_clicked = False
                for sel in ['button[aria-label="Login"]', 'button:has-text("Login")', 'button:has-text("Log in")', 'a:has-text("Login")', 'a:has-text("Log in")']:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.click()
                        login_clicked = True
                        time.sleep(1.5)
                        break
                if not login_clicked:
                    page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button, a');
                            for (const btn of buttons) {
                                const t = (btn.textContent || '').trim().toLowerCase();
                                const l = (btn.getAttribute('aria-label') || '').toLowerCase();
                                if (t === 'login' || t === 'log in' || l === 'login' || l === 'log in') { btn.click(); return true; }
                            }
                            return false;
                        }
                    """)
                    time.sleep(1.5)

                # Click Sign Up link
                signup_link = None
                for sel in ['button:has-text("Sign Up")', 'button:has-text("Sign up")', 'a:has-text("Sign Up")', 'a:has-text("Sign up")', 'button:has-text("New to OneCompiler")', 'a:has-text("New to OneCompiler")']:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        signup_link = loc.first
                        break
                if not signup_link:
                    page.evaluate("""
                        () => {
                            const els = document.querySelectorAll('button, a');
                            for (const el of els) {
                                const t = (el.textContent || '').trim().toLowerCase();
                                if (t.includes('sign up') || t.includes('new to onecompiler') || t.includes('create new account')) { el.click(); return true; }
                            }
                            return false;
                        }
                    """)
                    time.sleep(1)
                if signup_link:
                    signup_link.click()
                    time.sleep(1)

                # Fill name
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
                    browser.close()
                    return None

                # Fill email
                email_filled = False
                for sel in ['input[id="email"]', 'input[type="email"]', 'input[placeholder*="email" i]']:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.fill(email)
                        email_filled = True
                        break
                if not email_filled:
                    logger.error("Could not find email input")
                    browser.close()
                    return None

                # Fill password
                pw_filled = False
                for sel in ['input[id="password"]', 'input[type="password"]', 'input[placeholder*="password" i]']:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.fill(password)
                        pw_filled = True
                        break
                if not pw_filled:
                    logger.error("Could not find password input")
                    browser.close()
                    return None

                # Solve Turnstile
                turnstile_ok = _wait_for_turnstile(page, timeout=CONFIG.get('turnstile_timeout', 30))
                if not turnstile_ok:
                    logger.warning("Turnstile unsolved, submitting anyway...")
                time.sleep(1)

                # Submit
                submit_btn = None
                for sel in ['button:has-text("Sign Up"):not([disabled])', 'button:has-text("Sign up"):not([disabled])']:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        submit_btn = loc.first
                        break
                if not submit_btn:
                    logger.error("No submit button found")
                    browser.close()
                    return None
                submit_btn.click()
                time.sleep(3)

                # Wait for OTP field
                otp_field_visible = False
                try:
                    page.wait_for_selector('input[id="otp"], input[placeholder*="OTP"], input[placeholder*="otp"]', timeout=10000)
                    otp_field_visible = True
                except Exception:
                    otp_field_visible = page.evaluate("() => !!document.querySelector('input[id=\"otp\"], input[placeholder*=\"OTP\" i]')")
                if not otp_field_visible:
                    logger.error("OTP field never appeared")
                    browser.close()
                    return None

                # Get OTP from temp email
                if not mail:
                    logger.error("No mail object for OTP retrieval")
                    browser.close()
                    return None
                otp = mail.get_otp(timeout=CONFIG.get('otp_timeout', 90))
                if not otp:
                    logger.error("No OTP received")
                    browser.close()
                    return None
                logger.info(f"OTP: {otp}")

                # Fill OTP
                otp_filled = False
                for sel in ['input[id="otp"]', 'input[placeholder*="OTP" i]']:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        loc.first.fill(otp)
                        otp_filled = True
                        break
                if not otp_filled:
                    logger.error("Could not find OTP input")
                    browser.close()
                    return None

                _wait_for_turnstile(page, timeout=CONFIG.get('turnstile_timeout', 30))
                time.sleep(1)

                # Finish signup
                finish_btn = None
                for sel in ['button:has-text("Finish Sign Up")', 'button:has-text("Finish sign up")', 'button:has-text("Verify")', 'button:has-text("Confirm")']:
                    loc = page.locator(sel)
                    if loc.count() > 0 and loc.first.is_visible():
                        finish_btn = loc.first
                        break
                if not finish_btn:
                    logger.error("No finish button found")
                    browser.close()
                    return None
                finish_btn.click()
                time.sleep(5)

                # Extract token
                stored_token = extract_token(page)
                if stored_token and len(stored_token) > 20:
                    logger.info(f"Token: {stored_token[:50]}...")
                    browser.close()
                    return stored_token

                try:
                    page.wait_for_url('**/chat**', timeout=10000)
                except Exception:
                    pass

                stored_token = extract_token(page)
                if stored_token and len(stored_token) > 20:
                    logger.info(f"Token: {stored_token[:50]}...")
                    browser.close()
                    return stored_token

                logger.warning(f"No token found (URL: {page.url})")
                browser.close()
                return None

            except Exception as e:
                logger.error(f"Error: {e}")
                try:
                    browser.close()
                except Exception:
                    pass
                return None

    except Exception as e:
        logger.error(f"Browser launch error: {e}")
        return None


def _write_account(email, password, token=None):
    with _file_lock:
        with open('output/accounts.txt', 'a') as f:
            f.write(f"{email}:{password}\n")
        if token:
            with open('output/tokens.txt', 'a') as f:
                f.write(f"{token}\n")


def _create_account(index):
    global _success_count

    pw_chars = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
    pw = [random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), random.choice('0123456789')] + random.choices(pw_chars, k=14)
    random.shuffle(pw)
    password = ''.join(pw)

    mail = TempEmail()
    time.sleep(random.uniform(0, 2))
    if not mail.create_account():
        return

    email = mail.email

    result = signup(email, password, mail)

    if result:
        token = result if isinstance(result, str) else "SUCCESS"
        with _counter_lock:
            _success_count += 1
        _write_account(email, password, token)


def main():
    global _success_count

    count = CONFIG.get('count', 1)
    threads = min(CONFIG.get('threads', 1), count)

    print(f"\nOneCompiler Account Generator | {count} accounts, {threads} thread(s)")

    _success_count = 0
    Path('output').mkdir(exist_ok=True)

    if threads <= 1:
        for i in range(1, count + 1):
            _create_account(i)
            if i < count:
                time.sleep(2)
    else:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = {}
            for i in range(1, count + 1):
                futures[executor.submit(_create_account, i)] = i
                if i < count:
                    time.sleep(1.5)
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Crashed: {e}")

    print(f"\n{_success_count} accounts created successfully")
    print(f"Output: output/accounts.txt | output/tokens.txt")


if __name__ == "__main__":
    main()

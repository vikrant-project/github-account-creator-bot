# GitHub Account Creator Bot 🤖⚡

> A powerful Telegram bot that automates GitHub account creation with OTP verification, token generation, billing setup, card injection, and GitHub Pro upgrade — all from a single Telegram command.

---

## ✨ What It Does

GitHub Account Creator Bot automates the entire GitHub signup pipeline through a Telegram interface. Send one command and it handles everything: creates a temporary email, registers on GitHub, verifies OTP, generates a full-permission API token, sets up billing, injects credit cards, and attempts a GitHub Pro upgrade.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| **Auto Account Creation** | Full GitHub signup automation via Selenium headless Chrome |
| **Multi TempMail Support** | TempMail Library → 1SecMail → TempMail.org → Backup (fallback chain) |
| **OTP Auto-Detection** | Polls email inbox and extracts 6 or 8 digit OTP automatically |
| **Full Token Generation** | Creates GitHub PAT with all scopes (repo, codespace, workflow, etc.) |
| **Billing Setup** | Auto-fills billing info and injects cards from `card.txt` |
| **GitHub Pro Upgrade** | Attempts Pro upgrade after card is approved |
| **Persistent Storage** | Accounts saved to `accounts.json`, approved users to `approve.txt` |
| **Bulk Creation** | Create 1–500 accounts in sequence with 10s delay between each |
| **Admin Controls** | Approve users, view stats, test email services |
| **Channel Logging** | All created accounts auto-posted to your Telegram channel |

---

## 📋 Prerequisites

- **Python 3.8+**
- **Google Chrome** installed
- **ChromeDriver** matching your Chrome version at `/usr/local/bin/chromedriver`
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)

### Install System Dependencies (Ubuntu)

```bash
sudo apt update
sudo apt install -y google-chrome-stable chromium-chromedriver python3-pip
sudo ln -s /usr/bin/chromedriver /usr/local/bin/chromedriver
```

---

## 🔑 Configuration

Before running, edit these values at the top of `bot.py`:

```python
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
PASSWORD = "YourDefaultPassword@123"
ADMIN_IDS = [YOUR_TELEGRAM_USER_ID]
CHANNEL_ID = YOUR_CHANNEL_ID  # Channel where accounts are posted
```

> 💡 Get your Telegram user ID from [@userinfobot](https://t.me/userinfobot)

---

## 🛠 Setup

### 1. Clone the Repository

```bash
git clone https://soulcrack-spoofs-admin@bitbucket.org/soulcrack-spoofs/github-account-creator-bot.git
cd github-account-creator-bot
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Add Cards

Create a `card.txt` file with one card per line:

```
4111111111111111|12|25|123
5500005555555559|06|26|456
```

### 4. Run the Bot

```bash
python bot.py
```

---

## 🎮 Commands

| Command | Access | Description |
|---|---|---|
| `/start` | Everyone | Show help and command list |
| `/github <amount>` | Approved | Create 1–500 GitHub accounts |
| `/accounts` | Approved | View all your created accounts |
| `/upload_cards` | Approved | Upload a `card.txt` file |
| `/approve <user_id>` | Admin | Approve a user |
| `/stats` | Admin | View bot statistics |
| `/test_email` | Admin | Test TempMail services |
| `/clear_accounts` | Approved | Clear your account list |

### Examples

```
/github 1       → Create 1 account
/github 10      → Create 10 accounts in sequence
/accounts       → View all your accounts with buttons
/approve 123456 → Approve user with ID 123456
```

---

## 📧 TempMail Fallback Chain

The bot tries email services in this order until one works:

```
1. TempMail Library   ──► Primary (best OTP support)
        │ fails
        ▼
2. 1SecMail API       ──► Secondary
        │ fails
        ▼
3. TempMail.org API   ──► Tertiary
        │ fails
        ▼
4. Backup Generator   ──► Last resort (no OTP)
```

---

## ⚙️ How the Pipeline Works

```
/github 5
   │
   ▼
For each account:
   │
   ├── 1. Create temp email (fallback chain)
   ├── 2. Open GitHub signup via headless Chrome
   ├── 3. Fill email, password, username
   ├── 4. Wait for OTP email → extract OTP
   ├── 5. Enter OTP → verify account
   ├── 6. Login and create repo + codespace
   ├── 7. Generate full-permission GitHub token
   ├── 8. Save account to accounts.json
   ├── 9. Post to Telegram channel
   ├── 10. Fill billing info
   ├── 11. Inject cards from card.txt
   ├── 12. Attempt GitHub Pro upgrade
   └── 13. Wait 10s → next account
```

---

## 🗂 Project Structure

```
github-account-creator-bot/
├── bot.py                  # Main bot — all logic in one file
├── approve.txt             # Auto-created — approved user IDs
├── accounts.json           # Auto-created — all created accounts
├── card.txt                # Optional — cards for billing injection
├── requirements.txt        # Python dependencies
└── README.md
```

---

## 🚢 Deployment

### Run in Background (Linux)

```bash
nohup python bot.py > bot.log 2>&1 &
```

### Run with Screen

```bash
screen -S ghbot
python bot.py
# Detach: Ctrl+A then D
# Reattach: screen -r ghbot
```

### Run with PM2

```bash
pm2 start bot.py --interpreter python3 --name github-bot
pm2 save
pm2 startup
```

---

## ⚠️ Legal Disclaimer

This tool is intended for **educational purposes and legitimate automation research** only. Users are solely responsible for ensuring their usage complies with [GitHub's Terms of Service](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service) and all applicable laws. Automated account creation may violate platform policies.

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first.

---

<p align="center">Automate everything. 🤖⚡</p>
# Telegram Computer Repair Booking Bot

&#x20;&#x20;

A simple Telegram bot for appointments. Clients can pick a day and time, share their contact, and receive confirmations. Administrators see incoming requests and can approve or deny them.

## Features

- ✅ Bilingual support (English & Russian)
- 📅 Select next weekday and time slot
- 📲 Share contact via Telegram button or manual entry
- 🔔 Admin notifications with approve/deny inline buttons
- 💾 In‑memory storage (easy to extend to a database)

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites

- Python 3.8 or higher
- A Telegram bot token (get one via [@BotFather](https://t.me/BotFather))
- Administrator chat ID (your Telegram user ID you can use /myid command)

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/FaulinV/tg-appointment-bot.git
   cd tg-appointment-bot
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # on Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Open the `bot.py` file in your editor.
2. Replace the placeholder values:
   ```python
   TOKEN = 'PASTE_YOUR_API_TOKEN_HERE'
   ADMIN_CHAT_ID = 'PASTE_YOUR_ADMIN_CHAT_ID_HERE'
   ```
3. Save your changes.

## Usage

Run the bot:

```bash
python bot.py
```

Interact with your bot on Telegram:

1. Start the bot: `/start`
2. Choose **Book Repair** to schedule an appointment.
3. Follow prompts: pick day, time, enter name, share contact.
4. Administrator receives a notification and can **Confirm** or **Deny**.

## Project Structure

```
├── bot.py           # Main bot script
├── requirements.txt # Python dependencies
├── start_bot.bat    # Windows start script (optional)
└── README.md        # This guide
```

## Contributing

Pull requests and issues are welcome! Feel free to open an issue or submit patches.

## License

This project is licensed under the MIT License.

---

*Developed by Zhan Kornilov*


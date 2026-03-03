# Discord Bot Setup Guide

Brian Bot sends a daily counter message in a specified channel at a configured time.

This guide will help you set up Brian Bot using Python.

## Prerequisites

* Python **3.13.7** installed
* `pip` installed

---

## 1. Install Required Python Packages

```bash
pip install discord.py
pip install python-dotenv
pip install tzdata
```

---

## 2. Create a Discord Application

1. Go to the **Discord Developer Portal**:
   [https://discord.com/developers/applications](https://discord.com/developers/applications)

2. Click **New Application** and give it a name.

3. Navigate to the **Bot** section and click **Add Bot**.

---

### Get Your Bot Token

1. In your bot settings, go to:
   **Bot → Token**

2. Click **Reset Token** (if necessary).

3. Click **Copy** to copy your bot token.

---

### Create a `.env` File

In your project root:

```bash
cp .env.example .env
```

Open the `.env` file and replace:

```env
DISCORD_TOKEN=YOUR_DISCORD_TOKEN_HERE
```

With your copied token:

```env
DISCORD_TOKEN=your_actual_token_here
```

> ⚠️ Keep your bot token secret. Never share it publicly.

---

## 3. Invite the Bot to Your Server

1. In your application settings, go to:
   **OAuth2 > OAuth2 URL Generator**

2. Under **Scopes**, select:

   * `applications.commands`
   * `bot`

3. Scroll down to **Bot Permissions** and select:

   * ✅ View Channels
   * ✅ Send Messages
   * ✅ Use Slash Commands

4. Copy the generated URL and open it in your browser.

5. Select the server you want to invite your bot to and click **Authorize**.

---

## Run Your Bot

Once your `.env` is configured and your bot is invited:

```bash
python bot.py
```

Your bot should now appear **online** and be ready to respond to commands.

---

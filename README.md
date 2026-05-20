<div align="center">

# ✨ Starvell Cardinal

<p>
  <a href="https://t.me/StarvellCardinal">📢 Channel</a> •
  <a href="https://t.me/StarvellPlugins">🧩 Plugins</a> •
  <a href="https://t.me/embedium">👤 Author</a> •
  <a href="https://github.com/etheriumflipper/StarvellCardinal">💻 GitHub</a>
</p>

<p>
  <img src="https://img.shields.io/badge/Starvell-Automation-1f6feb?style=for-the-badge" alt="Starvell Automation" />
  <img src="https://img.shields.io/badge/Telegram-Bot-2ea44f?style=for-the-badge" alt="Telegram Bot" />
  <img src="https://img.shields.io/badge/Linux-Systemd-f2cc60?style=for-the-badge" alt="Linux Systemd" />
</p>

<h3>Starvell Cardinal is a Telegram bot for Starvell automation</h3>

<p>⚙️ Clean Cardinal • 🔄 Auto Updates • 🧩 Plugin System • 🛠️ One-Command Install</p>

</div>

> Starvell Cardinal is a Telegram bot for Starvell automation. Starvell Cardinal helps manage orders, lots, notifications, plugins and updates from one control panel.

Starvell Cardinal is built for sellers who want a clean Telegram workflow around Starvell. The project focuses on fast setup, automated order handling, plugin support, GitHub-based updates and Linux hosting with `systemd`.

If you are searching for `Starvell Cardinal`, this is the main public GitHub repository with the current install script, source code, releases and update mechanism.

Quick links:

- GitHub: https://github.com/etheriumflipper/StarvellCardinal
- Telegram channel: https://t.me/StarvellCardinal
- Telegram plugins: https://t.me/StarvellPlugins
- Author: https://t.me/embedium

## ⚡ One Command Install

```bash
wget https://raw.githubusercontent.com/etheriumflipper/StarvellCardinal/main/install.sh -O install.sh && bash install.sh
```

## 🚀 Quick Start

### 🐧 Linux / VPS

Install with one command:

```bash
wget https://raw.githubusercontent.com/etheriumflipper/StarvellCardinal/main/install.sh -O install.sh && bash install.sh
```

Service management after install:

```bash
sudo systemctl status starvell-cardinal
sudo systemctl restart starvell-cardinal
sudo systemctl stop starvell-cardinal
sudo journalctl -u starvell-cardinal -f
```

### 🪟 Windows

```bash
git clone https://github.com/etheriumflipper/StarvellCardinal.git
cd StarvellCardinal
Setup.bat
Start.bat
```

## 🧠 What Starvell Cardinal Can Do

- ⚙️ Automate work with `Starvell.com`
- 📦 Manage lots and products
- 📨 Track orders and messages
- 🔔 Send Telegram notifications
- 🛠️ Run first setup through a guided wizard
- 🔄 Check for updates and notify about new versions
- 🧩 Support a separate plugin system

## 🔄 Auto Updates

Starvell Cardinal can check for updates on startup and in the background.

When a new version appears in the repository:

- 👀 the bot detects the new `VERSION`
- 📨 admins receive a Telegram notification
- 🏷️ the message shows the current and new version
- 🔘 the bot offers an `Update now` button
- ⌨️ you can also use the `/update` command

Important: to trigger update detection, increase `VERSION` in [version.py](version.py) before publishing a new release.

## 📥 Install From Repository

If you want a manual install:

```bash
git clone https://github.com/etheriumflipper/StarvellCardinal.git
cd StarvellCardinal
sudo bash install.sh
```

The installer:

- 📦 installs dependencies
- 🐍 creates a virtual environment
- 🧭 runs `first_setup.py`
- 🔌 creates a `systemd` service
- 🟢 launches the bot in autonomous mode

## 🧷 First Launch

During setup the bot asks for:

1. `Bot Token` from `@BotFather`
2. password for bot access
3. `session_cookie` from `Starvell.com`

After the setup wizard finishes, it creates `configs/_main.cfg` and starts the service automatically.

## 🗂️ Project Structure

```text
StarvellCardinal/
├── main.py
├── first_setup.py
├── version.py
├── install.sh
├── start.sh
├── api/
├── bot/
├── configs/
├── docs/
├── plugins/
└── storage/
```

`plugins/` stays empty in the public version so you can deploy a clean Cardinal and add your own plugins separately.

## 🛠️ Development

- 🧠 Bot logic: `bot/`
- 🌐 API integration: `api/`
- 🧩 Plugin system: `bot/plugins/` and `plugins/`
- 📘 Plugin API docs: [docs/PLUGINS_API.md](docs/PLUGINS_API.md)

## 🔗 Links

- 👤 Author: [@embedium](https://t.me/embedium)
- 📢 Telegram channel: [@StarvellCardinal](https://t.me/StarvellCardinal)
- 🧩 Plugins: [@StarvellPlugins](https://t.me/StarvellPlugins)
- 💻 GitHub: [etheriumflipper/StarvellCardinal](https://github.com/etheriumflipper/StarvellCardinal)
- 🌍 Platform: [Starvell.com](https://starvell.com)

## 📄 License

The project is distributed under the [MIT](LICENSE) license.

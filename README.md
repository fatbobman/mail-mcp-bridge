# Mail MCP Bridge

> Connect macOS Mail to AI through Model Context Protocol (MCP)

**Mail MCP Bridge** enables AI assistants (like Claude, ChatGPT) to directly access and analyze your macOS Mail emails. Simply copy a Message-ID from Mail and paste it to AI — no manual email exporting needed.

[🇨🇳 中文版](README_zh.md)

## 🎯 What & Why

**The Problem**: Much of real-world communication happens through email — project collaborations, client communications, business negotiations, technical support. Manually exporting emails for AI analysis is tedious and inefficient.

**The Solution**: Mail MCP Bridge lets AI directly read your emails through a simple workflow:

- Copy Message-ID from Mail (one keyboard shortcut)
- Paste to AI
- AI analyzes email content instantly

**Use Cases**:

- 📋 Track project progress via email threads
- 💼 Extract key information from business communications
- 🔍 Summarize long email conversations
- 📊 Extract structured data (requirements, feedback, commitments)
- 🤝 Review conversation history

**Focus**: Plain text content extraction only (no attachments, no HTML) — perfect for AI analysis.

## ✨ Features

- 📧 **Direct Access** - AI reads your emails through MCP protocol
- 🧵 **Thread Support** - Retrieve entire conversations with one Message-ID
- ⚡ **Fast** - Millisecond-level query response
- 🎯 **Pure Text** - Clean text extraction, optimized for AI
- 🔒 **Privacy First** - Runs locally, emails never leave your Mac

## 🚀 Quick Start

### Prerequisites

- macOS 12.0+ (with Mail app)
- Python 3.9+
- MCP-compatible AI assistant (e.g., Claude Desktop)

### Installation

```bash
# Clone the repository
git clone https://github.com/fatbobman/mail-mcp-bridge.git
cd mail-mcp-bridge

# Install MCP dependencies
pip3 install mcp
```

### Configure Claude Desktop

1. **Find config location**:

   ```bash
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. **Edit config** (create if doesn't exist):

   ```json
   {
     "mcpServers": {
       "mail": {
         "command": "python3",
         "args": [
           "/path/to/mail-mcp-bridge/mail_mcp_server.py"
         ]
       }
     }
   }
   ```

   **Important**: Replace `/path/to/mail-mcp-bridge` with your actual project path.

3. **Restart Claude Desktop** (quit completely, then reopen)

### Setup Mail Quick Action

Add a "Copy Message-ID" button to Mail app:

**Video Demo** (30 seconds setup):

[![Watch demo video](https://github.com/user-attachments/assets/7ede277f-41ef-4898-ad8b-3014d5854b19)](https://github.com/user-attachments/assets/7ede277f-41ef-4898-ad8b-3014d5854b19)

**Step-by-Step**:

1. Open **Automator** (`⌘ + Space`, type "Automator")

2. Create new **Quick Action**:
   - File → New (`⌘ + N`)
   - Select "Quick Action"
   - Workflow receives current: **no input**
   - in: **Mail.app**

3. Add **Run Shell Script** action:
   - Search "Run Shell Script" in left panel
   - Drag to workflow area
   - Shell: `/bin/bash**

4. Copy script content:

   ```bash
   cat automator_script.sh
   ```

   Paste entire output into Automator script area

5. Save as **"Copy Message-ID"**

6. (Optional) Assign keyboard shortcut:
   - System Settings → Keyboard → Keyboard Shortcuts
   - Services → Mail → "Copy Message-ID"
   - Add shortcut (e.g., `⌘ + ⇧ + C`)

**Test It**:

1. Open Mail app
2. Select any email
3. Press your keyboard shortcut (if configured)
4. You should hear a sound confirming Message-ID copied

## 📖 Usage

### Basic Workflow

```
1. Select email in Mail
2. Press your keyboard shortcut (e.g., ⌘⇧C)
3. Paste Message-ID to AI
```

### Example Conversations

**Read Single Email**:

```
You: Please analyze this email: <message-id@example.com>

AI: I'll read that email for you...
[AI reads and analyzes the email content]
```

**Read Email Thread**:

```
You: What's the full conversation for <message-id@example.com>?

AI: I'll retrieve the entire thread...
[AI shows all emails in the conversation]
```

**Real-World Use Case**:

```
You: Please summarize all communication with our business partner,
including their requirements, promised timelines, and action items.

AI: I'll read the relevant email threads and extract key information...
[AI analyzes email content, organizes project progress, commitments, and action items]
```

## 🛠️ MCP Tools

| Tool | Description |
|------|-------------|
| `get_email_path` | Get single email file path |
| `get_thread_paths` | Get all paths in email thread |
| `read_email` | Read single email content |
| `read_thread` | Read entire email thread |

📖 **[→ Detailed API Documentation](TOOLS.md)**

## 🏗️ How It Works

```
┌─────────────┐
│  Mail App   │ Select email → Copy Message-ID (⌘⇧C)
└──────┬──────┘
       │
       ↓ Message-ID
┌─────────────┐
│MCP Server   │ 1. Query Mail SQLite database
│             │ 2. Locate .emlx file by ROWID
│             │ 3. Parse email content
│             │ 4. Extract plain text
└──────┬──────┘
       │
       ↓ Structured Data
┌─────────────┐
│ AI Assistant│ Analyze email content
└─────────────┘
```

🔧 **[→ Technical Architecture](ARCHITECTURE.md)**

## 🐛 Troubleshooting

### MCP server not found

**Solution**:

```bash
# Verify the path in claude_desktop_config.json
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop (quit completely, then reopen)
```

### Email not found

**Possible causes**:

1. Message-ID format incorrect (must include `< >`)
2. Email deleted from Mail
3. Email in different Mail account database

### Permission denied

**Solution**:

```bash
# Make scripts executable
chmod +x *.py *.sh
```

## 🔒 Privacy & Security

- ✅ **Local Processing**: All operations run locally on your Mac
- ✅ **No External Servers**: No data sent to external servers
- ✅ **No Telemetry**: No analytics or tracking
- ✅ **Read-Only**: Only reads email data, never modifies

## 📚 Documentation

- **[TOOLS.md](TOOLS.md)** - Complete API reference for all MCP tools
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture and database structure
- **[README_zh.md](README_zh.md)** - 中文文档

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions welcome! Please feel free to submit a Pull Request.

## 🌟 Acknowledgments

- Built for the MCP (Model Context Protocol) ecosystem
- Inspired by the need to bridge email and AI
- Tested with Claude Desktop on macOS 26 (Tahoe)

## 📮 Contact

- **Issues**: <https://github.com/fatbobman/mail-mcp-bridge/issues>
- **Author**: Fatbobman (Xu Yang)

## ☕ Buy Me a Coffee

If you find this project helpful, consider buying me a coffee!

[![Buy Me A Coffee](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/fatbobman)

---

**Made with ❤️ for the AI community**

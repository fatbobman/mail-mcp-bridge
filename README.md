# Mail MCP Bridge

> Connect macOS Mail to AI through Model Context Protocol (MCP)

**Mail MCP Bridge** enables AI assistants (like Claude, ChatGPT) to directly access and analyze your macOS Mail emails. Simply copy a Message-ID from Mail and paste it to AI — no manual email exporting needed.

[🇨🇳 中文版](README_zh.md)

## 🎯 Primary Use Case

**Core Value: Let AI analyze email text content and track project progress**

This project focuses on extracting and analyzing **plain text email content**, making it ideal for:

- **📋 Project Progress Tracking** - Analyze email threads with sponsors, clients, and partners
- **💼 Business Communication Analysis** - Extract key information, action items, and timelines
- **🔍 Email Summarization** - Quickly understand the core content of long emails or threads
- **📊 Data Extraction** - Extract structured information from emails (requirements, feedback, commitments)
- **🤝 Conversation History Review** - View complete email threads to understand communication context

**Note:** This project focuses on text content extraction and does not process attachments, images, or formatted HTML. For AI analysis, plain text is the most effective input format.

## 💡 Why I Built This

I've been exploring ways to deeply integrate AI into various aspects of my work and life. In practice, I've found that AI-assisted project management and communication summarization is particularly valuable.

However, much of real-world communication happens through email—everything from project collaborations and client communications to business negotiations and technical support. On macOS, email files (particularly email threads) are scattered across different directories. The traditional approach of exporting individual emails for AI analysis is inefficient and unfriendly to active projects.

To solve this problem, I created **Mail MCP Bridge**:
- One-click Message-ID retrieval (via Mail Quick Action)
- MCP tools based on Message-ID to quickly extract structured plain text email content
- Enable AI to seamlessly track project progress, analyze communication history, and extract key information

In short, this project bridges the gap between macOS Mail and AI assistants, making email a first-class citizen in the AI workflow.

## ✨ Features

- **📧 Direct Email Access** - AI can read your emails through MCP protocol
- **🧵 Thread Support** - Retrieve entire email conversations with one Message-ID
- **🔍 Fast & Efficient** - Query emails by Message-ID in milliseconds
- **🎯 Pure Text Output** - Clean text extraction, perfect for AI analysis
- **⚡ Easy to Use** - Quick Action in Mail app to copy Message-ID
- **🔒 Privacy First** - Runs locally, emails never leave your Mac

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

#### Configure MCP Server for Claude Desktop

1. **Find Claude Desktop config location:**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. **Edit the config file** (create if it doesn't exist):

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

**Important:** Replace `/path/to/mail-mcp-bridge` with your actual project path.

3. **Restart Claude Desktop** (quit completely, then reopen)

> **Note:** This project has been tested on macOS 26 (Tahoe). It should work on macOS 12.0+, but other versions have not been tested yet.

### Setup Mail Quick Action

Follow these steps to add a "Copy Message-ID" action to Mail:

1. **Open Automator**
   - Press `⌘ + Space` and type "Automator"
   - Or find it in `/Applications/Automator.app`

2. **Create New Quick Action**
   - File → New (or `⌘ + N`)
   - Select "Quick Action" (or "Service" on older macOS)
   - Click "Choose"

3. **Configure Quick Action**
   - Workflow receives current: **email messages**
   - in: **Mail.app**
   - Check: "Output replaces selected text"

4. **Add Shell Script Action**
   - Search for "Run Shell Script" in the left panel
   - Drag it to the workflow area
   - Shell: `/bin/bash`
   - Pass input: **as arguments**

5. **Copy Script Content**
   ```bash
   cat automator_script.sh
   ```
   - Copy the entire output
   - Paste into the script area in Automator

6. **Save the Quick Action**
   - File → Save (or `⌘ + S`)
   - Name: **Copy Message-ID**
   - It will be saved to `~/Library/Services/`

7. **Assign Keyboard Shortcut** (Optional)
   - System Settings → Keyboard → Keyboard Shortcuts
   - Select: Services → Mail
   - Find: "Copy Message-ID"
   - Click and add your preferred shortcut (e.g., `⌘ + ⇧ + C`)

**Setup Preview:**

![Automator Setup](images/automatic-setup.webp)

**Test It:**
1. Open Mail app
2. Select any email
3. Use your keyboard shortcut (if configured)
4. You should hear a sound confirming the Message-ID was copied
5. Check your clipboard - the Message-ID should be there, ready to paste to AI

> **Note:** macOS notifications may not appear depending on your system settings, but the sound confirms it worked.

**Demo Video:**

https://github.com/user-attachments/assets/7ede277f-41ef-4898-ad8b-3014d5854b19

> **Note:** In the video above, the Quick Action is triggered via right-click menu for demonstration purposes. In daily use, a keyboard shortcut is more convenient.

## 📖 Usage

### Basic Workflow

1. **Select email** in Mail app
2. **Press** ⌘⇧C (or right-click → Copy Message-ID)
3. **Paste** the Message-ID to AI

### Example Conversations

**Read Single Email:**
```
You: Please analyze this email: <message-id@example.com>

AI: I'll read that email for you...
[AI reads and analyzes the email content]
```

**Read Email Thread:**
```
You: What's the full conversation for <message-id@example.com>?

AI: I'll retrieve the entire thread...
[AI shows all emails in the conversation]
```

**Real-World Use Case:**
```
You: Please summarize all communication with our business partner,
including their requirements, promised timelines, and action items.

AI: I'll read the relevant email threads and extract key information...
[AI analyzes email content, organizes project progress, commitments, and action items]
```

## 🛠️ MCP Tools

The MCP server provides 4 tools:

### 1. `get_email_path`
Get the file path of a single email by Message-ID.

**Parameters:**
- `message_id` (string) - RFC Message-ID, e.g., `<abc@example.com>`

**Returns:**
```json
{
  "success": true,
  "file_path": "/path/to/email.emlx"
}
```

### 2. `get_thread_paths`
Get all email file paths in a conversation thread.

**Parameters:**
- `message_id` (string) - Any Message-ID from the thread

**Returns:**
```json
{
  "success": true,
  "thread_size": 3,
  "file_paths": [
    "/path/to/email1.emlx",
    "/path/to/email2.emlx",
    "/path/to/email3.emlx"
  ]
}
```

### 3. `read_email`
Parse and read a single email's plain text content.

**Parameters:**
- `message_id` (string) - RFC Message-ID

**Returns:**
```json
{
  "success": true,
  "subject": "Email Subject",
  "from": "Sender <sender@example.com>",
  "to": "Recipient <recipient@example.com>",
  "date": "Date string",
  "body_text": "Plain text email body",
  "headers": {...}
}
```

### 4. `read_thread`
Parse and read entire email thread.

**Parameters:**
- `message_id` (string) - Any Message-ID from the thread

**Returns:**
```json
{
  "success": true,
  "thread_size": 3,
  "emails": [
    {/* Email 1 */},
    {/* Email 2 */},
    {/* Email 3 */}
  ]
}
```

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

### Technical Details

- **Mail Database**: `~/Library/Mail/V10/MailData/Envelope Index` (SQLite)
- **Email Storage**: `~/Library/Mail/V10/{Account}/{Mailbox}.mbox/.../{ROWID}.emlx`
- **Key Discovery**: `messages.ROWID` = filename (not `remote_id`!)

## 📁 Project Structure

```
mail-mcp-bridge/
├── get_email_path.py       # Get single email file path
├── get_thread_paths.py      # Get email thread paths
├── parse_email.py           # Parse .emlx to plain text
├── mail_mcp_server.py       # MCP server (main)
├── automator_script.sh      # Mail Quick Action script
├── README.md                # This file
└── README_zh.md             # Chinese version
```

## ⚙️ Configuration

### MCP Server Config

The MCP server is configured in:
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

Configuration example:
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

**Note:** Update the path to match your actual installation directory.

## 🐛 Troubleshooting

### Issue: MCP server not found
**Solution:**
```bash
# Verify the path in claude_desktop_config.json
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Restart Claude Desktop (quit completely, then reopen)
```

### Issue: Email not found
**Possible causes:**
1. Message-ID format incorrect (must include `< >`)
2. Email deleted from Mail
3. Email in different Mail account database

### Issue: Permission denied
**Solution:**
```bash
# Make scripts executable
chmod +x *.py *.sh
```

## 🔒 Privacy & Security

- ✅ **Local Processing**: All operations run locally on your Mac
- ✅ **No External Servers**: No data sent to external servers
- ✅ **No Telemetry**: No analytics or tracking
- ✅ **Read-Only**: Only reads email data, never modifies

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🌟 Acknowledgments

- Built for the MCP (Model Context Protocol) ecosystem
- Inspired by the need to bridge email and AI
- Tested with Claude Desktop on macOS 26 (Tahoe)

## 📮 Contact

- **Issues**: https://github.com/fatbobman/mail-mcp-bridge/issues
- **Author**: Fatbobman (Xu Yang)

---

**Made with ❤️ for the AI community**

# Mail MCP Bridge - Technical Architecture

## Overview

Mail MCP Bridge consists of 4 main Python modules that work together to provide email access to AI assistants.

```
┌─────────────────────────────────────────────────────────────┐
│                     Mail MCP Bridge                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐      ┌─────────────────┐              │
│  │  Mail App       │      │   AI Assistant  │              │
│  │  (macOS)        │◄────►│   (Claude/...)  │              │
│  └────────┬────────┘      └─────────────────┘              │
│           │                                                   │
│           │ Message-ID                                       │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              MCP Server (mail_mcp_server.py)           ││
│  │  ┌─────────────────────────────────────────────────┐   ││
│  │  │  Tool 1: get_email_path                         │   ││
│  │  │  Tool 2: get_thread_paths                        │   ││
│  │  │  Tool 3: read_email                              │   ││
│  │  │  Tool 4: read_thread                             │   ││
│  │  └─────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────┘│
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Core Modules                               ││
│  │  ┌────────────────────┐                               ││
│  │  │ get_email_path.py  │ → Query SQLite → Get .emlx path││
│  │  ├────────────────────┤                               ││
│  │  │ get_thread_paths.py │ → Query conversation → Get paths││
│  │  ├────────────────────┤                               ││
│  │  │ parse_email.py     │ → Parse .emlx → Extract text  ││
│  │  └────────────────────┘                               ││
│  └─────────────────────────────────────────────────────────┘│
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Mail Data Storage                          ││
│  │  ┌──────────────────┐    ┌──────────────────────────┐  ││
│  │  │ Envelope Index   │    │ Email Files             │  ││
│  │  │ (SQLite DB)      │    │ ~/Library/Mail/.../*.emlx│  ││
│  │  │                  │    │                          │  ││
│  │  │ • messages       │    │ • Raw email source      │  ││
│  │  │ • conversation_id│    │ • Headers + body        │  ││
│  │  │ • ROWID = file   │    │ • Attachments           │  ││
│  │  └──────────────────┘    └──────────────────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Mail Database Structure

### Database Location

**Path**: `~/Library/Mail/V10/MailData/Envelope Index`
**Format**: SQLite
**Version**: V10 (macOS 12.0 Monterey - macOS 26 Tahoe, 2021-2025+)

**Note**: The V10 version has been stable for over 4 years across multiple macOS releases.

### Database Schema

#### `messages` Table

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key **= filename!** |
| `global_message_id` | INTEGER | Foreign key to `message_global_data.ROWID` |
| `mailbox` | INTEGER | Foreign key to `mailboxes.ROWID` |
| `conversation_id` | INTEGER | Thread identifier (groups related emails) |
| `date_sent` | TIMESTAMP | Email sent timestamp |
| `remote_id` | INTEGER | IMAP UID (NOT the filename!) |

#### `message_global_data` Table

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `message_id_header` | TEXT | RFC Message-ID (e.g., `<abc@example.com>`) |

#### `mailboxes` Table

| Column | Type | Description |
|--------|------|-------------|
| `ROWID` | INTEGER | Primary key |
| `url` | TEXT | Mailbox location (e.g., `imap://UUID/INBOX`) |

### 🔑 Key Discovery

**Email filename = `messages.ROWID`**, NOT `remote_id`!

This is a critical finding - many online documentation sources incorrectly reference `remote_id`. The actual filename on disk is the SQLite ROWID.

**Example**:

- `ROWID = 12345` → File is `12345.emlx`
- `remote_id = 67890` → Irrelevant for file location

---

## Email File Storage

### Directory Structure

```
~/Library/Mail/V10/
├── {Account-UUID-1}/           # Email account
│   ├── INBOX.mbox/             # Mailbox folder
│   │   ├── {ROWID}.emlx        # Email file
│   │   ├── {ROWID}.emlx
│   │   └── ...
│   ├── Archive.mbox/
│   │   └── ...
│   └── Sent.mbox/
│       └── ...
└── {Account-UUID-2}/
    └── ...
```

**Path Construction**:

```
~/Library/Mail/V10/{account_uuid}/{mailbox_name}.mbox/{ROWID}.emlx
```

### .emlx File Format

Apple's .emlx format is a simple text format:

```
Line 1:         File size in bytes (decimal number)
Line 2+:        Raw RFC 5322 email content
                (headers + body)
Last few lines: Apple plist metadata (XML)
```

**Example**:

```
3842
Received: from mail.example.com (192.168.1.1)
  by mail.apple.com with ESMTPS id 123ABC
  for <recipient@example.com>;
  Wed, 25 Dec 2024 10:30:00 +0800
Message-ID: <abc123@example.com>
Subject: Test Email
From: Sender <sender@example.com>
To: Recipient <recipient@example.com>
Content-Type: text/plain; charset=utf-8

This is the email body text.

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.mail.Mail</key>
    ...
</dict>
</plist>
```

**Parsing Strategy**:

1. Skip line 1 (size)
2. Read until `<?xml` or `<!DOCTYPE plist` detected
3. Parse email content using Python `email` module

---

## Query Flows

### get_email_path Flow

```
Input: Message-ID (<abc@example.com>)
    ↓
┌─────────────────────────────────────────┐
│ SQLite Query                            │
│                                         │
│ SELECT                                   │
│   m.ROWID,                              │
│   mb.url                                │
│ FROM messages m                          │
│ LEFT JOIN message_global_data mgd       │
│   ON m.global_message_id = mgd.ROWID    │
│ LEFT JOIN mailboxes mb                  │
│   ON m.mailbox = mb.ROWID               │
│ WHERE mgd.message_id_header = '<...>'   │
└─────────────────────────────────────────┘
    ↓
Result: ROWID=12345, url=imap://UUID/INBOX
    ↓
┌─────────────────────────────────────────┐
│ Parse mailbox URL                       │
│                                         │
│ imap://UUID/INBOX                       │
│   ↓ split & decode                      │
│ account_uuid = UUID                     │
│ mailbox_path = INBOX                    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Build file path                         │
│                                         │
│ ~/Library/Mail/V10/                     │
│   {UUID}/INBOX.mbox/12345.emlx          │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Verify file exists                      │
│                                         │
│ find /path/to/mbox -name 12345*.emlx    │
└─────────────────────────────────────────┘
    ↓
Output: /path/to/12345.emlx
```

### get_thread_paths Flow

```
Input: Message-ID (<abc@example.com>)
    ↓
┌─────────────────────────────────────────┐
│ Step 1: Get conversation_id             │
│                                         │
│ SELECT m.conversation_id                │
│ FROM messages m                          │
│ LEFT JOIN message_global_data mgd       │
│   ON m.global_message_id = mgd.ROWID    │
│ WHERE mgd.message_id_header = '<...>'   │
└─────────────────────────────────────────┘
    ↓
Result: conversation_id = 12345
    ↓
┌─────────────────────────────────────────┐
│ Step 2: Get all emails in thread        │
│                                         │
│ SELECT mgd.message_id_header            │
│ FROM messages m                          │
│ LEFT JOIN message_global_data mgd       │
│   ON m.global_message_id = mgd.ROWID    │
│ WHERE m.conversation_id = 12345         │
│ ORDER BY m.date_sent ASC                │
└─────────────────────────────────────────┘
    ↓
Result: [<msg1@...>, <msg2@...>, <msg3@...>]
    ↓
┌─────────────────────────────────────────┐
│ Step 3: Get path for each Message-ID    │
│                                         │
│ For each msg_id:                        │
│   call get_email_path(msg_id)           │
└─────────────────────────────────────────┘
    ↓
Output: [/path/to/msg1.emlx, ...]
```

---

## Module Details

### 1. get_email_path.py

**Purpose**: Locate email file by Message-ID

**Process**:

1. Accept RFC Message-ID (auto-add angle brackets if missing)
2. Query `messages` table in SQLite database
3. Match by `message_id_header` field
4. Get `ROWID` and `mailbox_url`
5. Parse mailbox URL to build directory path
6. Find .emlx file using `find` command
7. Return absolute path

**Key Features**:

- Auto-adds angle brackets to Message-ID
- Parses IMAP URL format
- Uses `find` command for file lookup (handles edge cases)
- 10-second timeout on file search

### 2. get_thread_paths.py

**Purpose**: Get all emails in a conversation thread

**Process**:

1. Accept any Message-ID from the thread
2. Query `conversation_id` via `get_conversation_id()`
3. Get all Message-IDs with same `conversation_id`
4. Sort by `date_sent` ASC
5. Call `get_email_path()` for each Message-ID
6. Return list of paths

**Thread Detection**:
Mail groups related emails using `conversation_id`:

- Same subject (Re:, Fwd:, etc.)
- Same participants (From, To, Cc)
- Reply/forward relationships
- Same thread in Mail UI

**Note**: May include duplicates if emails exist in multiple mailboxes (e.g., Inbox + Archive)

### 3. parse_email.py

**Purpose**: Parse .emlx file to plain text

**Process**:

1. Read .emlx file in binary mode
2. Skip first line (file size)
3. Extract email content until plist XML marker
4. Parse RFC 5322 format using `email` module
5. Decode headers using `email.header.decode_header()`
6. Extract `text/plain` body parts
7. Decode body using charset from `Content-Type`
8. Return structured JSON

**Supported Formats**:

- ✅ Plain text (`text/plain`)
- ✅ Multipart emails (extracts first `text/plain` part)
- ✅ Base64 encoded
- ✅ Quoted-printable encoding
- ✅ Various character encodings (UTF-8, GBK, ISO-8859-1, etc.)

**Not Supported**:

- ❌ HTML rendering
- ❌ Attachment extraction
- ❌ Embedded images
- ❌ Rich text/RTF

**Character Encoding**:

- Headers: Auto-detect and decode
- Body: Use charset from `Content-Type` header
- Fallback: UTF-8 with `errors='replace'` (shows � for invalid bytes)

### 4. mail_mcp_server.py

**Purpose**: MCP server that exposes tools to AI

**Process**:

1. Start stdio server
2. Register 4 tools with descriptions
3. Wait for tool calls from AI
4. Route to appropriate module
5. Return results as `TextContent` (JSON)

**Error Handling**:

- All tools return `{success: true/false}` structure
- Detailed error messages for debugging
- File not found reasons provided

---

## Data Flow Example

```
┌─────────────────────────────────────────────────────────────┐
│ User Action                                                  │
├─────────────────────────────────────────────────────────────┤
│ 1. Open Mail app                                            │
│ 2. Select email                                             │
│ 3. Press ⌘⇧C (Copy Message-ID Quick Action)                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Automator Quick Action                                      │
├─────────────────────────────────────────────────────────────┤
│ 1. Run AppleScript: `message id of msg`                     │
│ 2. Auto-wrap in angle brackets if needed                    │
│ 3. Copy to clipboard                                        │
│ 4. Play success sound (Glass.aiff)                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ User Interaction with AI                                    │
├─────────────────────────────────────────────────────────────┤
│ User: "Please analyze this email: <msg@id.com>"             │
│    ↓                                                         │
│ AI: Calls read_email tool                                   │
│    ↓                                                         │
│ MCP Server receives call                                    │
│    ↓                                                         │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ get_email_path.py                                    │   │
│ │   → Query SQLite database                            │   │
│ │   → Get ROWID = 12345                                │   │
│ │   → Find file: /path/to/12345.emlx                   │   │
│ └──────────────────────────────────────────────────────┘   │
│    ↓                                                         │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ parse_email.py                                       │   │
│ │   → Read .emlx file                                  │   │
│ │   → Extract Subject, From, To, Date                  │   │
│ │   → Decode body text                                 │   │
│ │   → Return JSON structure                            │   │
│ └──────────────────────────────────────────────────────┘   │
│    ↓                                                         │
│ MCP Server returns JSON to AI                               │
│    ↓                                                         │
│ AI analyzes email content and responds                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Performance

| Operation | Typical Time | Bottleneck |
|-----------|--------------|------------|
| `get_email_path` | 5-20ms | SQLite query + file system |
| `get_thread_paths` | 10-50ms | Multiple queries + file lookups |
| `read_email` | 10-30ms | File I/O + parsing |
| `read_thread` | 50-200ms | Depends on thread size |

**Optimizations**:

1. **SQLite indexes** on `message_id_header` and `conversation_id`
2. **File system cache** (macOS caches recently accessed files)
3. **Direct property access** - AppleScript's `message id` is instant (vs parsing source)

**Performance Tips**:

- Large threads (>50 emails) may take longer
- Repeated access to same emails benefits from OS cache
- Use `get_thread_paths` first if you need both paths and content

---

## Security Considerations

### Database Access

- **Read-only** - Never writes to Mail database
- **User permissions** - Requires same access as current user
- **No privilege escalation**

### File System

- **Standard macOS permissions**
- Follows macOS Mail's access model
- No network access

### MCP Protocol

- **stdio transport** - Local only, no network ports
- **Sandboxed** - AI controls when to call tools
- **No background processes**

### Data Handling

- **No persistence** - Doesn't cache or store email data
- **No telemetry** - No analytics or tracking
- **Local processing** - All operations on your Mac

---

## Troubleshooting

### Database Locked

**Symptom**: SQLite query fails with "database is locked"

**Cause**:

- Mail app is running and has database locked
- Mail is actively syncing emails

**Solution**:

- Close Mail app temporarily
- Or retry after Mail finishes syncing

### ROWID Changes

**Symptom**: File not found for existing ROWID

**Cause**:

- Mail rebuilt database (rare)
- Email was exported/imported

**Detection**: Check if file exists at expected path
**Solution**: ROWID may have changed, query database again

### Character Encoding Issues

**Symptom**: Garbled text in email body

**Cause**:

- Incorrect charset in email headers
- Email uses legacy encoding

**Solution**:

- Parser falls back to UTF-8 with replacement
- Shows � for undecodable bytes
- Open original email in Mail to verify content

---

## Future Considerations

### macOS Version Compatibility

- **Current**: V10 database (macOS 12-26)
- **Future**: If Apple changes database structure, update paths in:
  - `get_email_path.py`: Line 19-20
  - `get_thread_paths.py`: Line 19

### Potential Enhancements

- Add caching layer for frequently accessed emails
- Support for searching emails by content
- Export thread as single document
- Integration with other email clients (via standard formats)

---

## See Also

- [TOOLS.md](TOOLS.md) - Detailed API documentation for all MCP tools
- [README.md](README.md) - Quick start guide and usage examples

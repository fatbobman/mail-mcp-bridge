# Architecture

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

## Module Details

### 1. get_email_path.py

**Purpose**: Locate email file by Message-ID

**Process**:
1. Accept RFC Message-ID (e.g., `<user@host.com>`)
2. Query `messages` table in SQLite database
3. Match by `message_id_header` field
4. Get `ROWID` (this equals the filename!)
5. Find .emlx file in Mail directory structure
6. Return absolute path

**Key Discovery**: `messages.ROWID` is the filename, NOT `remote_id` (IMAP UID)

### 2. get_thread_paths.py

**Purpose**: Get all emails in a conversation thread

**Process**:
1. Accept any Message-ID from the thread
2. Query `messages` table by `conversation_id`
3. Get all `ROWID`s in that conversation
4. Find all corresponding .emlx files
5. Return list of paths (sorted chronologically)

**Note**: May include duplicates if emails exist in multiple mailboxes (e.g., Inbox + Archive)

### 3. parse_email.py

**Purpose**: Parse .emlx file to plain text

**Process**:
1. Read .emlx file (special format):
   ```
   Line 1: File size
   Lines 2+: Raw email source (RFC 5322)
   Last lines: Apple plist metadata (XML)
   ```
2. Skip first line (size)
3. Extract email content until plist starts
4. Use Python `email` module to parse
5. Decode headers (Subject, From, To, etc.)
6. Decode body (base64, quoted-printable)
7. Return structured JSON

**Supported**: Plain text emails only (no HTML rendering, no attachment extraction)

### 4. mail_mcp_server.py

**Purpose**: MCP server that exposes tools to AI

**Process**:
1. Start stdio server
2. Register 4 tools
3. Wait for tool calls from AI
4. Route to appropriate module
5. Return results as TextContent (JSON)

## Data Flow Example

```
User Action: Select email → Press ⌘⇧C

1. Automator Quick Action runs
2. Extract Message-ID from email source
3. Copy to clipboard
4. User pastes to AI: "Analyze <msg@id.com>"

AI Side:
5. Call read_email tool with Message-ID
6. MCP server receives call
7. get_email_path.py → Get file path
8. parse_email.py → Extract text
9. Return JSON to AI
10. AI analyzes content
```

## Performance

- **Query time**: ~0.08-0.1 seconds per email
- **Thread retrieval**: ~0.2-0.3 seconds for 5-email thread
- **Memory usage**: Minimal (on-demand processing)
- **Disk usage**: No caching, reads directly from Mail storage

## Security Considerations

- **Read-only**: Never modifies Mail database or files
- **Local only**: No network calls
- **No data persistence**: Doesn't store email data
- **Sandboxed**: MCP protocol limits tool access

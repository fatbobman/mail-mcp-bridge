# MCP Tools API Reference

Complete documentation for all 4 MCP tools provided by Mail MCP Bridge.

## Table of Contents

- [get_email_path](#1-get_email_path)
- [get_thread_paths](#2-get_thread_paths)
- [read_email](#3-read_email)
- [read_thread](#4-read_thread)
- [Error Handling](#error-handling)
- [Performance](#performance)

---

## 1. `get_email_path`

Get the absolute file path of a single email by Message-ID.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | ✅ | RFC Message-ID, e.g. `<abc@example.com>` |

**Note**: Angle brackets are optional - the tool will auto-add them if missing.

### Returns

**Success**:

```json
{
  "success": true,
  "message_id": "<abc@example.com>",
  "file_path": "/Users/xxx/Library/Mail/V10/UUID/INBOX.mbox/12345.emlx"
}
```

**Error**:

```json
{
  "success": false,
  "message_id": "<abc@example.com>",
  "error": "Email file not found",
  "possible_reasons": [
    "Message-ID does not exist",
    "Email file has been deleted",
    "Email is in a different Mail database version"
  ]
}
```

### Use Cases

- Debug email file location
- Custom email processing scripts
- Verify email existence

### Implementation Details

**Query Flow**:

```
Message-ID → SQLite: SELECT ROWID, mailbox_url
           WHERE message_id_header = '<...>'
         ↓
Parse mailbox URL → Build directory path
         ↓
find {mbox_path} -name {ROWID}*.emlx
         ↓
Return file path
```

**Database Tables Used**:

- `messages` - For ROWID and mailbox reference
- `message_global_data` - For Message-ID lookup
- `mailboxes` - For mailbox URL

---

## 2. `get_thread_paths`

Get file paths of all emails in a conversation thread.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | ✅ | Any Message-ID from the thread |

### Returns

**Success**:

```json
{
  "success": true,
  "message_id": "<abc@example.com>",
  "thread_size": 3,
  "file_paths": [
    "/path/to/email1.emlx",
    "/path/to/email2.emlx",
    "/path/to/email3.emlx"
  ]
}
```

**Error**:

```json
{
  "success": false,
  "message_id": "<abc@example.com>",
  "error": "Email thread not found or thread has no email files"
}
```

### Use Cases

- Analyze complete conversation history
- Thread-level email operations
- Email thread backup

### Implementation Details

**How it works**:

1. Query `conversation_id` from Message-ID
2. Find all emails with same `conversation_id`
3. Sort by `date_sent` ASC (chronological order)
4. Get file path for each email
5. Return sorted file paths

**SQL Query**:

```sql
-- Step 1: Get conversation_id
SELECT m.conversation_id
FROM messages m
LEFT JOIN message_global_data mgd ON m.global_message_id = mgd.ROWID
WHERE mgd.message_id_header = '<message-id@example.com>'

-- Step 2: Get all emails in thread
SELECT mgd.message_id_header
FROM messages m
LEFT JOIN message_global_data mgd ON m.global_message_id = mgd.ROWID
WHERE m.conversation_id = 12345
ORDER BY m.date_sent ASC
```

**What is a Thread?**

Mail groups related emails into conversations using `conversation_id`:

- Same subject (Re:, Fwd:)
- Same participants (From, To, Cc)
- Reply/forward relationships

---

## 3. `read_email`

Parse and read plain text content of a single email.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | ✅ | RFC Message-ID |

### Returns

**Success**:

```json
{
  "success": true,
  "message_id": "<abc@example.com>",
  "subject": "Project Update",
  "from": "Sender Name <sender@example.com>",
  "to": "Recipient Name <recipient@example.com>",
  "cc": "cc@example.com",
  "date": "Wed, 25 Dec 2024 10:30:00 +0800",
  "references": "<original@example.com> <prev@example.com>",
  "in_reply_to": "<prev@example.com>",
  "body_text": "Plain text email body..."
}
```

**Error**:

```json
{
  "success": false,
  "error": "Parse failed: ..."
}
```

### Use Cases

- AI email analysis
- Email content extraction
- Email summarization
- Content indexing

### Implementation Details

**What gets extracted**:

- ✅ Plain text body (`text/plain` parts only)
- ✅ Key headers (Subject, From, To, Cc, Date)
- ✅ Threading headers (References, In-Reply-To)
- ✅ Decoded header values (e.g. `=?UTF-8?B?...?=`)
- ❌ Attachments (skipped)
- ❌ HTML content (skipped)
- ❌ Embedded images (skipped)
- ❌ Rich text/RTF (skipped)
- ❌ Full raw headers (not included)

**Email Parsing Process**:

```
1. Read .emlx file
2. Skip first line (file size)
3. Extract email content (before plist XML)
4. Parse RFC 5322 format
5. Decode headers (charset detection)
6. Extract text/plain body
7. Decode body using charset from Content-Type
```

**Character Encoding**:

- Headers: Auto-detect and decode (UTF-8, GBK, ISO-8859-1, etc.)
- Body: Use charset from `Content-Type` header
- Fallback: UTF-8 with error replacement (�)

**Multipart Email Handling**:

- Walk through all MIME parts
- Skip attachments (`Content-Disposition: attachment`)
- Find first `text/plain` part
- Decode and return
- Ignore `text/html`, `image/*`, etc.

---

## 4. `read_thread`

Parse and read entire email thread.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message_id` | string | ✅ | Any Message-ID from the thread |

### Returns

**Success**:

```json
{
  "success": true,
  "message_id": "<abc@example.com>",
  "thread_size": 3,
  "emails": [
    {
      "success": true,
      "message_id": "<msg1@example.com>",
      "subject": "Re: Project Update",
      "from": "Alice <alice@example.com>",
      "to": "Bob <bob@example.com>",
      "cc": "",
      "date": "Mon, 23 Dec 2024 09:00:00 +0800",
      "references": "<original@example.com>",
      "in_reply_to": "",
      "body_text": "Hi Bob, how's the project going?"
    },
    {
      "success": true,
      "message_id": "<msg2@example.com>",
      "subject": "Re: Project Update",
      "from": "Bob <bob@example.com>",
      "to": "Alice <alice@example.com>",
      "cc": "",
      "date": "Tue, 24 Dec 2024 10:30:00 +0800",
      "references": "<original@example.com> <msg1@example.com>",
      "in_reply_to": "<msg1@example.com>",
      "body_text": "Making good progress..."
    },
    {
      "success": true,
      "message_id": "<msg3@example.com>",
      "subject": "Re: Project Update",
      "from": "Alice <alice@example.com>",
      "to": "Bob <bob@example.com>",
      "cc": "",
      "date": "Wed, 25 Dec 2024 15:45:00 +0800",
      "references": "<original@example.com> <msg1@example.com> <msg2@example.com>",
      "in_reply_to": "<msg2@example.com>",
      "body_text": "Great to hear!"
    }
  ]
}
```

**Error**:

```json
{
  "success": false,
  "message_id": "<abc@example.com>",
  "error": "Email thread not found or thread has no email files"
}
```

### Use Cases

- Conversation analysis
- Thread summarization
- Progress tracking across multiple emails
- Email thread visualization

### Implementation Details

**Process**:

1. Get all Message-IDs in thread (using `get_thread_paths` logic)
2. For each Message-ID:
   - Get file path
   - Parse email file
   - Extract structured data
3. Sort all emails by `date_sent` (already sorted from step 1)
4. Return array of email objects

**Each email object** has the same structure as `read_email` return value.

**Sorting**: Emails are returned in chronological order (oldest first).

---

## Error Handling

All tools follow this error response format:

```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

Additional fields may be included depending on the error:

- `message_id` - When Message-ID is provided
- `possible_reasons` - Array of likely causes (for `get_email_path`)

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Email file not found" | Message-ID doesn't exist or email deleted | Verify Message-ID format (`<...>`) |
| "Mail database not found" | Mail V10 database missing | Check Mail app version (requires macOS 12+) |
| "Parse failed" | Corrupted .emlx file | Open email in Mail app to verify |
| "Thread not found" | Message-ID invalid or not in a thread | Use single email tools instead |

---

## Performance

| Operation | Typical Time | Notes |
|-----------|--------------|-------|
| `get_email_path` | 5-20ms | SQLite query + file system lookup |
| `get_thread_paths` | 10-50ms | Depends on thread size |
| `read_email` | 10-30ms | File I/O + parsing |
| `read_thread` | 50-200ms | Depends on thread size and email content |

**Optimizations**:

- SQLite indexes on `message_id_header` and `conversation_id`
- File system cache (macOS)
- Direct property access in AppleScript (no email source parsing)

**Performance Tips**:

- Use `get_thread_paths` first if you need both paths and content
- Cache results if repeatedly accessing the same emails
- Large threads (>50 emails) may take longer

---

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture and database structure
- [README.md](README.md) - Quick start guide and usage examples

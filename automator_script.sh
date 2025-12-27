#!/bin/bash
# Mail Message-ID Copy Quick Action
# Copy the first Message-ID from selected emails in Mail.app
# Optimized: Processes first 10000 chars to handle longer email headers

osascript <<'EOF'
tell application "Mail"
    set selectedMessages to selection

    if (count of selectedMessages) is 0 then
        display notification "Please select an email first" with title "Copy Message-ID"
        do shell script "afplay /System/Library/Sounds/Basso.aiff"
        return
    end if

    -- Only get the first successful Message-ID
    -- (One ID is enough for read_thread to get entire conversation)
    repeat with msg in selectedMessages
        try
            -- Get email source
            set msgSource to source of msg

            -- Only take first 10000 characters (email headers can be longer)
            -- Performance optimization: Still processes large attachment emails quickly
            set msgHeader to ""
            try
                set sourceLen to length of msgSource
                if sourceLen > 10000 then
                    set msgHeader to text 1 thru 10000 of msgSource
                else
                    set msgHeader to msgSource
                end if
            on error
                set msgHeader to msgSource
            end try

            -- Extract Message-ID (case-insensitive)
            -- Supports both "Message-ID" and "Message-Id" formats
            set msgID to do shell script "echo " & quoted form of msgHeader & " | grep -iE 'Message-Id:[^<]*<[^>]+>' | sed -E 's/.*[Mm]essage-[Ii][dD]:[^<]*(<[^>]+>).*/\\1/' | head -1 | tr -d '\\r\\n'"

            if msgID is not "" then
                -- Found first valid Message-ID, copy and exit
                set the clipboard to msgID
                display notification msgID with title "✅ Message-ID Copied"
                do shell script "afplay /System/Library/Sounds/Glass.aiff"
                return
            end if

        on error errMsg
            -- Continue to next email if current one fails
        end try
    end repeat

    -- If all emails failed
    display notification "Could not extract Message-ID from selected emails" with title "❌ Extraction Failed"
    do shell script "afplay /System/Library/Sounds/Basso.aiff"
end tell
EOF

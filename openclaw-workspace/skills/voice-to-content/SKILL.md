---
name: voice_to_content
description: Convert voice notes and audio into multi-format content
emoji: "🎤"
requires:
  env:
    - DEEPGRAM_API_KEY
user-invocable: true
---

# Voice to Content Factory

Transform voice notes, podcasts, and audio recordings into polished multi-format content.

## Use Cases

1. **Founder voice notes** → Blog posts, social content
2. **Meeting recordings** → Key takeaways, action items
3. **Podcast episodes** → Show notes, clips, quotes
4. **Tutorial walkthroughs** → Written guides
5. **Brainstorm sessions** → Organized ideas

## Commands

### `/voice transcribe <audio-path>`
Transcribe audio to text.

**Process:**
1. Upload audio to Deepgram
2. Get timestamped transcription
3. Identify speakers (if multiple)
4. Clean up filler words (um, uh, like)
5. Format with paragraphs

**Output:**
```
TRANSCRIPTION
=============
Duration: 5:32
Speakers: 1

[00:00] Introduction to AgentARC security...
[00:45] The four-stage pipeline works like this...
[02:15] Let me show you a code example...
```

### `/voice blog <audio-path>`
Convert voice note to blog post.

**Process:**
1. Transcribe audio
2. Extract main points and structure
3. Expand into full paragraphs
4. Add code examples if mentioned
5. Apply BRAND_VOICE.md
6. Run through ai-trace-remover
7. Format for WordPress

### `/voice thread <audio-path>`
Convert to Twitter thread.

**Process:**
1. Transcribe audio
2. Extract key insights (5-10 points)
3. Format as thread with hooks
4. Add relevant code snippets
5. End with CTA

### `/voice social <audio-path>`
Convert to all social formats.

**Output:**
- Twitter thread
- LinkedIn post
- Instagram carousel script
- TikTok script (if visual enough)

### `/voice clips <audio-path>`
Extract quotable clips.

**Process:**
1. Transcribe with timestamps
2. Identify strong statements
3. Extract 15-60 second segments
4. Provide timestamps for video editing
5. Write captions for each clip

**Output:**
```
CLIP 1: "The security layer that should have existed"
Timestamp: 01:23 - 01:45
Caption: "Your AI agent can be jailbroken. Your funds shouldn't be at risk."

CLIP 2: "Honeypot detection in action"
Timestamp: 03:12 - 03:58
Caption: "Watch AgentARC catch a honeypot token in real-time."
```

### `/voice summary <audio-path>`
Quick summary of audio content.

**Output:**
- 3-5 bullet point summary
- Key quotes
- Action items (if any)
- Follow-up topics

### `/voice meeting <audio-path>`
Process meeting recording.

**Output:**
- Attendee summary
- Key decisions
- Action items with owners
- Follow-up topics
- Quotable moments

## Audio Quality Tips

For best results:
- Clear audio, minimal background noise
- Speak naturally (don't read scripts)
- Mention specific terms clearly
- Pause between topics
- State key points explicitly

## Integration Pipeline

Typical workflow:
```
Voice Note
    ↓
/voice transcribe
    ↓
/voice blog (or /voice social)
    ↓
/factcheck
    ↓
/humanize
    ↓
/seo optimize (for blog)
    ↓
/wp publish (or /post all)
```

## Supported Formats

- MP3
- WAV
- M4A
- MP4 (extracts audio)
- WebM

Max duration: 60 minutes (longer files split automatically)

## Speaker Identification

For multi-speaker audio:
1. Identifies distinct speakers
2. Labels as Speaker 1, Speaker 2, etc.
3. Can rename speakers after identification
4. Useful for interviews, podcasts, meetings

## Language Support

Primary: English
Also supports: Spanish, French, German, Portuguese, Japanese, Korean, Chinese

Specify with: `/voice transcribe <path> --lang es`

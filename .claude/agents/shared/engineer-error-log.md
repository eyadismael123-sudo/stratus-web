# Engineering Error Log — Stratus

Shared between Backend Engineer, Frontend Engineer, and Error Checker.
All engineers read this before every session.
Error Checker adds new patterns after every review.

## Active Patterns to Watch

### Python / FastAPI
- Always close SQLite connections after queries (use context managers)
- Always validate Telegram webhook inputs before processing
- Use async/await consistently — never mix sync and async
- Never hardcode API keys — always use environment variables

### Frontend / Next.js
- Always check Architect's API contract before connecting to backend
- Mobile-first — test on 375px before anything else
- Never skip loading and error states in UI components

### General
- Write error handling for every external API call
- Test edge cases: empty input, None, timeout, duplicate

## Learning History
[New entries added here after each Error Checker review session]


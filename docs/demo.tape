# Run from the repository root. Prerequisites: VHS 0.11.0, ttyd, ffmpeg, uv,
# and Python >=3.10. See docs/offline-receipt.md for reproduction limits.
Output docs/assets/terminal-demo.gif
Set Shell "bash"
Set FontSize 15
Set Width 860
Set Height 470
Set Theme "GruvboxDark"
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0
Set WaitTimeout 120s

Hide
Type "export PS1='> '; clear"
Enter
Wait+Line /^> ?$/
Show

Type "uv sync --group dev"
Enter
Wait+Line /^> ?$/
Sleep 2s

Type "uv run pytest"
Enter
Wait+Screen /[0-9]+ passed/
Wait+Line /^> ?$/
Sleep 2s

Type "uv run python -m receipts"
Enter
Wait+Screen /retry: duplicate_retry_suppressed/
Wait+Line /^> ?$/
Sleep 14s

# Guess the Lava — Python multiplayer game

A responsive browser-based multiplayer drawing and guessing game built with Python, Flask and Flask-SocketIO.

## Features
- Create a group and share a six-character invite code
- Maximum 11 players per room
- One randomly selected drawer per round
- Secret word visible only to the drawer
- Shared real-time drawing canvas
- Guessers receive +11 points for a correct guess (once per round)
- If nobody guesses before 80 seconds, every player including the drawer receives -11
- Live scoreboard, host controls and next-round flow
- Word bank: 168 unique words

## Run on Windows
1. Install Python 3.10 or newer.
2. Extract the ZIP folder.
3. Open PowerShell in the `guess_the_lava_python` folder.
4. Create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
5. Install packages:
   ```powershell
   pip install -r requirements.txt
   ```
6. Start:
   ```powershell
   python app.py
   ```
7. Open http://127.0.0.1:5000 in your browser.

## Play with friends
For same-Wi-Fi testing, run the server on one computer and let friends open `http://YOUR-COMPUTER-LAN-IP:5000`.
For friends on different networks, deploy the app to a public Python host with HTTPS and WebSocket support. The invite code is then shared with friends, who open the same app URL and enter it.

## Android APK / iPhone IPA
This folder is a Python web game, not a native mobile package. To produce installable APK/IPA files, package the web app in a mobile WebView shell or build a separate Kivy client and point it to a deployed server. Android APK can be built with Android tooling; iOS IPA requires macOS/Xcode and Apple signing. No APK or IPA is included in this source ZIP.

## Important limitations before public launch
- Rooms are stored in server memory and disappear when the server restarts.
- This starter is suitable for local testing and a prototype, not production hosting.
- Add persistent storage, room expiry, reconnection, moderation, rate limiting, HTTPS, and production security controls before public release.
- The server currently trusts a player's browser session ID; do not treat it as cheat-proof identity.
- Use a production WSGI/Socket.IO deployment configuration rather than Flask debug mode.

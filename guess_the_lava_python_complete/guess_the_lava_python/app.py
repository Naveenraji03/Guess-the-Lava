import json, random, string, threading, time
from pathlib import Path
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

ROOT = Path(__file__).parent
WORDS = json.loads((ROOT / "data" / "words.json").read_text(encoding="utf-8"))
app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-before-deployment"
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

rooms = {}
lock = threading.RLock()
MAX_PLAYERS = 11
ROUND_SECONDS = 80

def new_code():
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choice(alphabet) for _ in range(6))

def public_room(code):
    room = rooms[code]
    players = [
        {"id": sid, "name": p["name"], "score": p["score"],
         "is_drawer": sid == room.get("drawer_id")}
        for sid, p in room["players"].items()
    ]
    players.sort(key=lambda p: p["score"], reverse=True)
    return {
        "code": code, "players": players, "status": room["status"],
        "round": room["round"], "drawer_id": room.get("drawer_id"),
        "ends_at": room.get("ends_at"), "last_result": room.get("last_result", ""),
        "guessed_count": len(room.get("guessed", [])),
        "guessers_count": max(0, len(room["players"]) - 1)
    }

def broadcast_room(code):
    if code in rooms:
        socketio.emit("room_update", public_room(code), to=code)

def finish_round(code, unsolved=False):
    with lock:
        room = rooms.get(code)
        if not room or room["status"] != "playing":
            return
        if unsolved and len(room["guessed"]) == 0:
            for player in room["players"].values():
                player["score"] -= 11
            room["last_result"] = "Time is up! Nobody guessed correctly. Everyone gets -11 points."
        elif unsolved:
            room["last_result"] = "Time is up! Correct guessers keep their +11 points. No penalty this round."
        else:
            room["last_result"] = "All players guessed correctly! Round complete."
        room["status"] = "finished"
        room["word"] = None
        room["ends_at"] = None
    broadcast_room(code)
    socketio.emit("round_finished", {"message": room["last_result"]}, to=code)

def round_clock(code, round_number):
    while True:
        socketio.sleep(1)
        with lock:
            room = rooms.get(code)
            if not room or room["status"] != "playing" or room["round"] != round_number:
                return
            remaining = room["ends_at"] - time.time()
        socketio.emit("timer", {"remaining": max(0, int(remaining))}, to=code)
        if remaining <= 0:
            finish_round(code, unsolved=True)
            return

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("create_room")
def create_room(data):
    name = (data.get("name") or "").strip()[:18]
    if not name:
        emit("error_message", {"message": "Enter your player name."}); return
    with lock:
        code = new_code()
        while code in rooms:
            code = new_code()
        rooms[code] = {
            "host_id": request.sid, "players": {request.sid: {"name": name, "score": 0}},
            "status": "lobby", "round": 0, "word": None, "drawer_id": None,
            "ends_at": None, "guessed": [], "last_result": "",
            "drawer_queue": []
        }
        join_room(code)
    emit("joined_room", {"code": code, "player_id": request.sid, "is_host": True})
    broadcast_room(code)

@socketio.on("join_room")
def join_existing(data):
    code = (data.get("code") or "").strip().upper()
    name = (data.get("name") or "").strip()[:18]
    with lock:
        room = rooms.get(code)
        if not name:
            emit("error_message", {"message": "Enter your player name."}); return
        if not room:
            emit("error_message", {"message": "Group not found. Check the code."}); return
        if request.sid not in room["players"] and len(room["players"]) >= MAX_PLAYERS:
            emit("error_message", {"message": "This group is full (maximum 11 players)."}); return
        if room["status"] == "playing":
            emit("error_message", {"message": "A round is in progress. Join after this round."}); return
        room["players"][request.sid] = {"name": name, "score": room["players"].get(request.sid, {}).get("score", 0)}
        join_room(code)
    emit("joined_room", {"code": code, "player_id": request.sid, "is_host": room["host_id"] == request.sid})
    broadcast_room(code)

@socketio.on("start_round")
def start_round(data):
    code = (data.get("code") or "").upper()
    with lock:
        room = rooms.get(code)
        if not room or request.sid != room["host_id"]:
            emit("error_message", {"message": "Only the group host can start a round."}); return
        if room["status"] == "playing":
            emit("error_message", {"message": "A round is already running."}); return
        if len(room["players"]) < 2:
            emit("error_message", {"message": "At least 2 players are needed."}); return
        if not room["drawer_queue"] or room["round"] == 0:
            room["drawer_queue"] = list(room["players"].keys())
            random.shuffle(room["drawer_queue"])
        else:
            active_ids = set(room["players"].keys())
            room["drawer_queue"] = [sid for sid in room["drawer_queue"] if sid in active_ids]
            queued_ids = set(room["drawer_queue"])
            for sid in room["players"]:
                if sid not in queued_ids:
                    room["drawer_queue"].append(sid)
        drawer_id = room["drawer_queue"].pop(0)
        word = random.choice(WORDS)
        room.update(status="playing", round=room["round"] + 1, drawer_id=drawer_id,
                    word=word, ends_at=time.time() + ROUND_SECONDS, guessed=[], last_result="")
        round_number = room["round"]
        ends_at = room["ends_at"]
        drawer_name = room["players"][drawer_id]["name"]
    broadcast_room(code)
    socketio.emit("round_started", {"drawer_name": drawer_name, "seconds": ROUND_SECONDS}, to=code)
    socketio.emit("your_word", {"word": word}, to=drawer_id)
    socketio.start_background_task(round_clock, code, round_number)

@socketio.on("draw_stroke")
def draw_stroke(data):
    code = (data.get("code") or "").upper()
    room = rooms.get(code)
    if not room or room["status"] != "playing" or room["drawer_id"] != request.sid:
        return
    points = data.get("points", [])
    if not isinstance(points, list) or len(points) > 300:
        return
    socketio.emit("draw_stroke", {"points": points, "color": data.get("color", "#111827"),
                                  "width": min(18, max(1, float(data.get("width", 4))))}, to=code, include_self=False)

@socketio.on("clear_canvas")
def clear_canvas(data):
    code = (data.get("code") or "").upper()
    room = rooms.get(code)
    if room and room["status"] == "playing" and room["drawer_id"] == request.sid:
        socketio.emit("clear_canvas", {}, to=code)

@socketio.on("submit_guess")
def submit_guess(data):
    code = (data.get("code") or "").upper()
    guess = (data.get("guess") or "").strip()
    with lock:
        room = rooms.get(code)
        if not room or room["status"] != "playing" or request.sid == room["drawer_id"]:
            return
        if request.sid in room["guessed"]:
            emit("guess_feedback", {"correct": False, "message": "You already guessed this round."}); return
        if guess.casefold() == (room["word"] or "").casefold():
            room["guessed"].append(request.sid)
            room["players"][request.sid]["score"] += 11
            player_name = room["players"][request.sid]["name"]
            remaining = len(room["players"]) - 1 - len(room["guessed"])
            emit("guess_feedback", {"correct": True, "message": "Correct! +11 points."})
            socketio.emit("player_guessed", {"name": player_name, "remaining": remaining}, to=code, include_self=False)
            if remaining == 0:
                finish_round(code, unsolved=False)
            else:
                broadcast_room(code)
        else:
            emit("guess_feedback", {"correct": False, "message": "Not quite. Try again!"})

@socketio.on("disconnect")
def disconnect():
    with lock:
        for code, room in list(rooms.items()):
            if request.sid in room["players"]:
                name = room["players"][request.sid]["name"]
                del room["players"][request.sid]
                leave_room(code)
                if not room["players"]:
                    del rooms[code]
                    return
                if room["host_id"] == request.sid:
                    room["host_id"] = next(iter(room["players"]))
                if room["status"] == "playing" and request.sid in room["guessed"]:
                    room["guessed"].remove(request.sid)
                broadcast_room(code)
                socketio.emit("notice", {"message": f"{name} left the group."}, to=code)
                return

if __name__ == "__main__":
    print(f"Loaded {len(WORDS)} words.")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

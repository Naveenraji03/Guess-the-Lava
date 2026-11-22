const socket = io();
let roomCode = null, playerId = null, isHost = false, isDrawer = false;
let currentColor = "#111827", drawing = false, lastPoint = null, timerInterval = null;
const $ = id => document.getElementById(id);
const home = $("home"), game = $("game"), canvas = $("board"), ctx = canvas.getContext("2d");
function toast(message){const t=$("toast");t.textContent=message;t.classList.remove("hidden");setTimeout(()=>t.classList.add("hidden"),3000)}
function playerName(){return $("playerName").value.trim()}
function showGame(){home.classList.add("hidden");game.classList.remove("hidden");$("codeLabel").textContent=roomCode}
$("createBtn").onclick=()=>{if(!playerName())return toast("Enter your player name.");socket.emit("create_room",{name:playerName()})};
$("joinBtn").onclick=()=>{if(!playerName())return toast("Enter your player name.");socket.emit("join_room",{name:playerName(),code:$("roomCode").value})};
socket.on("joined_room",d=>{roomCode=d.code;playerId=d.player_id;isHost=d.is_host;showGame();$("shareBtn").onclick=async()=>{const inviteUrl=window.location.origin;const text=`Join my Guess the Lava game!\nOpen: ${inviteUrl}\nGroup code: ${roomCode}`;try{if(navigator.share){await navigator.share({title:"Guess the Lava",text,url:inviteUrl});return}}catch(error){if(error&&error.name=== "AbortError")return}try{await navigator.clipboard.writeText(text);toast("Invite link and code copied!")}catch(error){const textarea=document.createElement("textarea");textarea.value=text;textarea.style.position="fixed";textarea.style.opacity="0";document.body.appendChild(textarea);textarea.select();const copied=document.execCommand("copy");textarea.remove();toast(copied?"Invite link and code copied!":"Could not copy invite. Share group code: "+roomCode)}}});
socket.on("error_message",d=>toast(d.message));
socket.on("room_update",d=>{
 $("playerCount").textContent=`${d.players.length}/11`;$("roundNo").textContent=d.round;
 $("players").innerHTML=d.players.map(p=>`<div class="player"><div class="avatar">${escapeHtml(p.name[0]||"?")}</div><div class="pname"><b>${escapeHtml(p.name)}</b><small>${p.is_drawer&&d.status==="playing"?"DRAWING":""}</small></div><div class="score">${p.score} pts</div></div>`).join("");
 $("startBtn").classList.toggle("hidden",!isHost||d.status==="playing");
 if(d.status==="lobby"){$("wordLabel").textContent="Waiting for host…";$("timer").textContent="Lobby";$("tools").classList.add("hidden");$("guessArea").classList.add("hidden");$("result").classList.add("hidden")}
 if(d.status==="finished"){$("wordLabel").textContent="Round complete";$("timer").textContent="Finished";$("tools").classList.add("hidden");$("guessArea").classList.add("hidden");$("result").textContent=d.last_result;$("result").classList.remove("hidden");$("startBtn").classList.toggle("hidden",!isHost)}
 if(d.status==="playing"){isDrawer=d.drawer_id===playerId;$("wordLabel").textContent=isDrawer?"Your secret word is coming…":`Drawing: ${escapeHtml((d.players.find(p=>p.is_drawer)||{}).name||"Player")}`;$("tools").classList.toggle("hidden",!isDrawer);$("guessArea").classList.toggle("hidden",isDrawer);$("result").classList.add("hidden")}
});
socket.on("round_started",d=>{clearCanvas();$("timer").textContent=`${d.seconds}s`;toast(`${d.drawer_name} is drawing!`)});
socket.on("your_word",d=>{$("wordLabel").textContent=`Draw: ${d.word}`;toast("Your secret word: "+d.word)});
socket.on("timer",d=>$("timer").textContent=`${d.remaining}s`);
socket.on("round_finished",d=>{$("result").textContent=d.message;$("result").classList.remove("hidden")});
socket.on("guess_feedback",d=>toast(d.message));
socket.on("player_guessed",d=>toast(`${d.name} guessed correctly! ${d.remaining} left.`));
socket.on("notice",d=>toast(d.message));
$("startBtn").onclick=()=>socket.emit("start_round",{code:roomCode});
$("guessBtn").onclick=submitGuess;$("guessInput").addEventListener("keydown",e=>{if(e.key==="Enter")submitGuess()});
function submitGuess(){const guess=$("guessInput").value.trim();if(guess){socket.emit("submit_guess",{code:roomCode,guess});$("guessInput").value=""}}
document.querySelectorAll(".color").forEach(b=>b.onclick=()=>{currentColor=b.dataset.color;document.querySelectorAll(".color").forEach(x=>x.classList.remove("active"));b.classList.add("active")});
$("clearBtn").onclick=()=>{clearCanvas();socket.emit("clear_canvas",{code:roomCode})};
function point(e){const r=canvas.getBoundingClientRect();return {x:(e.clientX-r.left)*canvas.width/r.width,y:(e.clientY-r.top)*canvas.height/r.height}}
canvas.addEventListener("pointerdown",e=>{if(!isDrawer)return;drawing=true;lastPoint=point(e);canvas.setPointerCapture(e.pointerId)});
canvas.addEventListener("pointermove",e=>{if(!drawing||!isDrawer)return;const p=point(e);drawLine(lastPoint,p,currentColor,5);socket.emit("draw_stroke",{code:roomCode,points:[lastPoint,p],color:currentColor,width:5});lastPoint=p});
canvas.addEventListener("pointerup",()=>{drawing=false;lastPoint=null});canvas.addEventListener("pointercancel",()=>{drawing=false;lastPoint=null});
socket.on("draw_stroke",d=>{for(let i=1;i<d.points.length;i++)drawLine(d.points[i-1],d.points[i],d.color,d.width)});
socket.on("clear_canvas",clearCanvas);
function drawLine(a,b,color,width){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.strokeStyle=color;ctx.lineWidth=width;ctx.lineCap="round";ctx.lineJoin="round";ctx.stroke()}
function clearCanvas(){ctx.fillStyle="#fff";ctx.fillRect(0,0,canvas.width,canvas.height)}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
clearCanvas();

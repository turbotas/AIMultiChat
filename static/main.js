const socket = io();

// Join a chat room - you'll need to replace this with dynamic data
const chatId = 'room1';
const username = prompt("Enter your name:") || "Anonymous";
socket.emit('join', {chat_id: chatId, username: username});

// Listen for status and message events
socket.on('status', (data) => {
  const chatDiv = document.getElementById('chat');
  const p = document.createElement('p');
  p.textContent = data.msg;
  chatDiv.appendChild(p);
});

socket.on('message', (data) => {
  const chatDiv = document.getElementById('chat');
  const p = document.createElement('p');
  p.textContent = `${data.username}: ${data.message} [${data.timestamp}]`;
  chatDiv.appendChild(p);
});

function sendMessage() {
  const input = document.getElementById('messageInput');
  const message = input.value;
  if (message.trim() === "") return;

  socket.emit('message', {
    chat_id: chatId,
    username: username,
    message: message,
    // For now, we'll just send a placeholder sender_id
    sender_id: 0
  });
  input.value = "";
}

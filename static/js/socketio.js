var socketio = io();
const messages = document.getElementById("messages");


// Get the input field
var input = document.getElementById("myInput");

// Execute a function when the user presses a key on the keyboard
input.addEventListener("keypress", function(event) {
  // If the user presses the "Enter" key on the keyboard
  if (event.key === "Enter") {
    // Cancel the default action, if needed
    event.preventDefault();
    createMessage()
  }
});

function openChat(userId) {
    fetch(`/chat/${userId}`)
        .then(response => response.json())
        .then(data => {
            const chatBox = document.getElementById('chatBox');
            chatBox.innerHTML = ''; // Clear the chat box

            data.messages.forEach(msg => {
                const messageElement = document.createElement('p');
                messageElement.className = `chatMessage ${msg.sender === 'me' ? 'my-chat' : 'frnd-chat'}`;

                messageElement.innerHTML = `
                    <span>${msg.content}</span>
                    <span class="chat__msg-filler"></span>
                    <span class="msg-footer">
                        <span>${msg.timestamp}</span>
                        ${msg.sender === 'me' ? 
                            `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 15" width="16" height="15" aria-label="read" class="chat-icon--blue">
                                <path fill="currentColor"
                                    d="M15.01 3.316l-.478-.372a.365.365 0 0 0-.51.063L8.666 9.879a.32.32 0 0 1-.484.033l-.358-.325a.319.319 0 0 0-.484.032l-.378.483a.418.418 0 0 0 .036.541l1.32 1.266c.143.14.361.125.484-.033l6.272-8.048a.366.366 0 0 0-.064-.512zm-4.1 0l-.478-.372a.365.365 0 0 0-.51.063L4.566 9.879a.32.32 0 0 1-.484.033L1.891 7.769a.366.366 0 0 0-.515.006l-.423.433a.364.364 0 0 0 .006.514l3.258 3.185c.143.14.361.125.484-.033l6.272-8.048a.365.365 0 0 0-.063-.51z"></path>
                            </svg>` : ''}
                    </span>
                `;
                chatBox.appendChild(messageElement);
            });
        })
        .catch(error => console.error('Error:', error));
}

// Function to create and append a message element
const createMessage = (name, msg, isFile = false) => {
    let content;
    if (isFile) {
        content = `
        <div class="text">
            <span>
                <strong>${name}</strong>: <a href="${msg}" target="_blank">File</a>
            </span>
            <span class="muted">
                ${new Date().toLocaleString()}
            </span>
        </div>
        `;
    } else {
        content = `
        <div class="text">
            <span>
                <strong>${name}</strong>: ${msg}
            </span>
            <span class="muted">
                ${new Date().toLocaleString()}
            </span>
        </div>
        `;
    }
    messages.innerHTML += content;
};

// Handle incoming messages
socketio.on("message", (data) => {
    if (data.message.startsWith("file:")) {
        const fileUrl = data.message.replace("file:", "");
        createMessage(data.name, fileUrl, true);
    } else {
        createMessage(data.name, data.message);
    }
});

// Send text message
const sendMessage = () => {
    const message = document.getElementById("message");
    if (message.value == "") return;
    console.log("Sending message:", message.value);
    socketio.emit("message", {data: message.value});
    message.value = "";
};

// Send file
const sendFile = () => {
    const fileInput = document.getElementById("file-input");
    if (fileInput.files.length === 0) return;

    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload_file', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            socketio.emit("message", {data: `file:${data.file_url}`});
        }
    });

    fileInput.value = ""; // Clear the file input
};
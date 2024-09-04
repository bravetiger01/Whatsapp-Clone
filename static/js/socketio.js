var socketio = io();
const messages = document.getElementById("messages");


// Get the input field
var input = document.getElementById("messages");

// Execute a function when the user presses a key on the keyboard
input.addEventListener("keypress", function(event) {
  // If the user presses the "Enter" key on the keyboard
  if (event.key === "Enter") {
    // Cancel the default action, if needed
    console.log("Sent!")
    event.preventDefault();
    sendMessage()
  }
});



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
        console.log(data)
        createMessage(data.name, fileUrl, true);
    } else {
        console.log(data)
        createMessage(data.name, data.message);
    }
});

// Send text message
const sendMessage = () => {
    const message = document.getElementById("messages");
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
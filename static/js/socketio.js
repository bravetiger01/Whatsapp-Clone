

var socketio = io();




// Get the input field
var input = document.getElementById("messages");
var groupname;
var groupcode;

// Execute a function when the user presses a key on the keyboard
input.addEventListener("keypress", function(event) {
// If the user presses the "Enter" key on the keyboard
if (event.key === "Enter") {
    // Cancel the default action, if needed
    event.preventDefault();
    groupname = groupnamefunc()
    groupcode = groupcodefunc()
    user_id = document.getElementById("user_id").innerHTML
    console.log(group,groupcode,user_id)
    sendMessage(group,groupcode,user_id)
    console.log("Sent!")
}
});



// Send text message
const sendMessage = (group,groupcode,user_id) => {
    const message = document.getElementById("messages");
    if (message.value == "") return;
    console.log("Sending message:", message.value);
    console.log(groupcode)
    content = {
        data: message.value, 
        group_name:group,
        group_code:groupcode,
        sender_id:user_id
    }
    socketio.emit("message", content);

    message.value = "";
};


// Function to create and append a message element
function createMessage(content,sender_id,sender_name) {
    
    var message = "";
    const chatBox = document.getElementById('chatBox');
    user_id = document.getElementById("user_id").innerHTML
    console.log(content)
    if (sender_id == user_id){
        message = `
        <div>
            <p class="chatMessage my-chat">
                <span>${content} </span>
                <span class="chat__msg-filler"> </span>
                <span class="msg-footer">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 15" width="16" height="15"
                        aria-label="read" class="chat-icon--blue">
                        <path fill="currentColor"
                            d="M15.01 3.316l-.478-.372a.365.365 0 0 0-.51.063L8.666 9.879a.32.32 0 0 1-.484.033l-.358-.325a.319.319 0 0 0-.484.032l-.378.483a.418.418 0 0 0 .036.541l1.32 1.266c.143.14.361.125.484-.033l6.272-8.048a.366.366 0 0 0-.064-.512zm-4.1 0l-.478-.372a.365.365 0 0 0-.51.063L4.566 9.879a.32.32 0 0 1-.484.033L1.891 7.769a.366.366 0 0 0-.515.006l-.423.433a.364.364 0 0 0 .006.514l3.258 3.185c.143.14.361.125.484-.033l6.272-8.048a.365.365 0 0 0-.063-.51z">
                        </path>
                    </svg>
                </span>
                <button aria-label="Message options" class="chat__msg-options"><svg
                        xmlns="http://www.w3.org/2000/svg" viewBox="0 0 19 20" width="19" height="20"
                        class="chat__msg-options-icon">
                        <path fill="currentColor"
                            d="M3.8 6.7l5.7 5.7 5.7-5.7 1.6 1.6-7.3 7.2-7.3-7.2 1.6-1.6z">
                        </path>
                    </svg>
                </button>
            </p>
        </div>`
    }

    else{
        message=`<p class="chatMessage frnd-chat">
                <span>${content}</span>
                <span class="chat__msg-filler2"> </span>
                <span class="msg-footer">
                    <span style="margin: 1px;">${sender_name}</span>
                </span>
                <button aria-label="Message options" class="chat__msg-options"><svg
                        xmlns="http://www.w3.org/2000/svg" viewBox="0 0 19 20" width="19" height="20"
                        class="chat__msg-options-icon">
                        <path fill="currentColor"
                            d="M3.8 6.7l5.7 5.7 5.7-5.7 1.6 1.6-7.3 7.2-7.3-7.2 1.6-1.6z">
                        </path>
                    </svg>
                </button>
            </p>
        </div>
        `;
    }
        
    chatBox.innerHTML += message;
    

    
    
    
     
};

// Handle incoming messages
socketio.on("messages", (data) => {
    console.log(data);
    
    var current_group = document.getElementById("Shayan").innerHTML;
    var group_parts = current_group.split(" - ");
    var current_group_name = group_parts[0].trim();  // Group name
    var current_group_code = group_parts[1].trim();  // Group code (if available)



    console.log(current_group_code);
    console.log(data['group_code']);
    if (current_group_code == data['group_code']){
        createMessage(content=data['message'], sender_id=data['sender_id'],name=data['name']);
    }
    
});





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

// function leaveGroup() {
//     group = document.getElementById("Shayan").innerHTML
//     group = group.split(" - ")[0];
//     console.log(group)
//     if (confirm("Are you sure you want to leave this group?")) {
//         fetch(`/leave_group/${group}`, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//                 'X-CSRFToken': '{{ csrf_token() }}'  // Make sure CSRF protection is in place
//             },
//         }).then(response => {
//             if (response.ok) {
//                 window.location.reload();  // Reload the page after leaving the group
//             } else {
//                 alert('Failed to leave the group.');
//             }
//         });
//     }
// }
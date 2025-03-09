const socket = io('https://yourbackend.com');  // URL of your deployed backend
let userRoom = null;
let token = localStorage.getItem('jwt_token');  // Store token after login

// Function to initialize WebSocket and join a room after login
function initWebSocket() {
    if (token) {
        socket.emit('connect', { token: token });
    } else {
        alert('Please log in first!');
    }
}

// Function to send message to a user
function sendMessage() {
    const messageText = document.getElementById('message-text').value;
    const receiver = document.getElementById('receiver').value;  // Assume receiver is selected
    
    // Send message to the receiver's room
    socket.emit('send_message', {
        sender: 'current_user',
        receiver: receiver,
        message: messageText
    });
}

// Handle message received in the room
socket.on('receive_message', function (data) {
    const sender = data.sender;
    const message = data.message;
    displayMessage(sender, message);
});

// Display the received message
function displayMessage(sender, message) {
    const messageContainer = document.createElement('div');
    messageContainer.innerText = `${sender}: ${message}`;
    document.getElementById('message-container').appendChild(messageContainer);
}

// Function to handle room creation
async function createRoom() {
    try {
        const response = await fetch('/create_room', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({})
        });
        const data = await response.json();
        if (data.room) {
            userRoom = data.room;
            console.log(`Room created: ${userRoom}`);
        }
    } catch (error) {
        console.error("Error creating room:", error);
    }
}

// Fetch the users for messaging
async function fetchUsers() {
    try {
        const response = await fetch('/users', {  // Endpoint to get users
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        const data = await response.json();
        displayUsers(data.users);
    } catch (error) {
        console.error("Error fetching users:", error);
    }
}

// Display the list of users
function displayUsers(users) {
    const userList = document.getElementById('user-list');
    users.forEach(user => {
        const userItem = document.createElement('li');
        userItem.innerText = user.username;
        userItem.onclick = () => selectUserToMessage(user);
        userList.appendChild(userItem);
    });
}

// Select a user to message
function selectUserToMessage(user) {
    document.getElementById('receiver').value = user.username;
}

// Search function for users
document.getElementById('search-bar').addEventListener('input', function (e) {
    const searchTerm = e.target.value.toLowerCase();
    const userItems = document.querySelectorAll('#user-list li');
    userItems.forEach(item => {
        if (item.innerText.toLowerCase().includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
});

// Initialize WebSocket connection when the page loads
window.onload = function () {
    initWebSocket();
    fetchUsers();
};
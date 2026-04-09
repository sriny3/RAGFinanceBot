// FinBot Frontend Application JavaScript

const API_BASE = "http://localhost:8000/api";

// State
let currentUser = null;
let users = [];
let userCollections = [];

// Initialize app
document.addEventListener("DOMContentLoaded", async () => {
    console.log("FinBot Frontend Initializing...");
    
    // Check if already logged in
    const savedUser = localStorage.getItem("currentUser");
    if (savedUser) {
        const user = JSON.parse(savedUser);
        await loginUser(user.username);
    } else {
        // Show login screen
        await loadUsers();
        showLoginScreen();
    }
});

// Load users for login dropdown
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/users`);
        if (!response.ok) throw new Error("Failed to load users");
        
        users = await response.json();
        
        // Populate dropdown
        const select = document.getElementById("userSelect");
        select.innerHTML = '<option value="">Select a user to login...</option>';
        users.forEach(user => {
            const option = document.createElement("option");
            option.value = user.username;
            option.textContent = `${user.name} (${user.role})`;
            select.appendChild(option);
        });
        
        // Populate login buttons
        const usersList = document.getElementById("usersList");
        usersList.innerHTML = "";
        users.forEach(user => {
            const btn = document.createElement("button");
            btn.className = "user-btn";
            btn.onclick = () => loginUser(user.username);
            btn.innerHTML = `
                <strong>${user.name}</strong>
                <small>${user.role} • ${user.department}</small>
            `;
            usersList.appendChild(btn);
        });
    } catch (error) {
        console.error("Error loading users:", error);
        showError("Failed to load user list. Check that the backend is running.");
    }
}

// Show login screen
function showLoginScreen() {
    document.getElementById("loginScreen").style.display = "flex";
    document.getElementById("chatInterface").style.display = "none";
}

// Show chat interface
function showChatInterface() {
    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("chatInterface").style.display = "flex";
}

// Login user
async function loginUser(username) {
    try {
        const response = await fetch(`${API_BASE}/users/${username}`);
        if (!response.ok) throw new Error("User not found");
        
        currentUser = await response.json();
        userCollections = currentUser.accessible_collections;
        
        // Save to localStorage
        localStorage.setItem("currentUser", JSON.stringify(currentUser));
        
        // Update UI
        document.getElementById("userName").textContent = currentUser.name;
        document.getElementById("userRole").textContent = currentUser.role;
        document.getElementById("userDept").textContent = currentUser.department;
        
        // Update collections display
        updateCollectionsDisplay();
        
        // Clear chat and show interface
        document.getElementById("chatMessages").innerHTML = `
            <div class="system-message">
                <p><strong>Welcome, ${currentUser.name}!</strong></p>
                <p>You are logged in as: <strong>${currentUser.role}</strong></p>
                <p>You have access to: <strong>${userCollections.join(", ")}</strong></p>
                <p style="margin-top: 1rem;">You can now ask questions about FinSolve. Try:</p>
                <ul>
                    <li>"What are our company policies?"</li>
                    <li>"How much leave am I entitled to?"</li>
                </ul>
            </div>
        `;
        
        showChatInterface();
        document.getElementById("queryInput").focus();
    } catch (error) {
        console.error("Error logging in:", error);
        showError(`Failed to login user: ${error.message}`);
    }
}

// Logout user
function logout() {
    currentUser = null;
    userCollections = [];
    localStorage.removeItem("currentUser");
    document.getElementById("userSelect").value = "";
    showLoginScreen();
}

// Switch user via dropdown
async function switchUser() {
    const username = document.getElementById("userSelect").value;
    if (username) {
        await loginUser(username);
    }
}

// Update collections display
function updateCollectionsDisplay() {
    const collectionsDiv = document.getElementById("collections");
    collectionsDiv.innerHTML = "";
    
    userCollections.forEach(collection => {
        const tag = document.createElement("div");
        tag.className = "collection-tag";
        tag.textContent = collection.toUpperCase();
        collectionsDiv.appendChild(tag);
    });
}

// Send query
async function sendQuery() {
    const queryInput = document.getElementById("queryInput");
    const query = queryInput.value.trim();
    
    if (!query) return;
    if (!currentUser) {
        showError("Please login first");
        return;
    }
    
    // Add user message to chat
    addMessageToChat(query, "user");
    queryInput.value = "";
    
    // Show loading indicator
    showLoadingIndicator(true);
    
    try {
        // Call API
        const response = await fetch(`${API_BASE}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_role: currentUser.role,
                query: query,
                user_id: currentUser.username,
            }),
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Hide loading
        showLoadingIndicator(false);
        
        // Display guardrail warnings if any
        if (result.guardrail_warnings && result.guardrail_warnings.length > 0) {
            showGuardrailWarnings(result.guardrail_warnings);
        } else {
            hideGuardrailWarnings();
        }
        
        // Handle RBAC denial
        if (result.rbac_denied) {
            addMessageToChat(
                `🔒 <strong>Access Denied</strong><br>${result.answer}<br><em>(Reason: ${result.rbac_reason})</em>`,
                "assistant"
            );
            return;
        }
        
        // Build message with metadata
        let message = result.answer;
        
        if (result.sources && result.sources.length > 0) {
            message += `<div class="sources"><strong>📄 Sources:</strong>`;
            result.sources.forEach(source => {
                message += `<div class="source-item"><strong>${source.document}</strong> (Page ${source.page_number})`;
                if (source.section_title) {
                    message += ` - ${source.section_title}`;
                }
                message += `</div>`;
            });
            message += `</div>`;
        }
        
        // Add metadata
        message += `<div class="message-metadata">`;
        message += `<span class="route-badge">${result.route}</span>`;
        if (result.guardrail_flags && result.guardrail_flags.length > 0) {
            message += `<span style="color: #f44336; font-weight: bold;">⚠️ Flags: ${result.guardrail_flags.join(", ")}</span>`;
        }
        message += `</div>`;
        
        // Add message
        addMessageToChat(message, "assistant");
    } catch (error) {
        console.error("Error:", error);
        showLoadingIndicator(false);
        addMessageToChat(
            `❌ <strong>Error:</strong> ${error.message}`,
            "assistant"
        );
        showError("Failed to process query. Is the backend running on localhost:8000?");
    }
}

// Add message to chat
function addMessageToChat(content, role) {
    const messagesDiv = document.getElementById("chatMessages");
    
    const messageDiv = document.createElement("div");
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.innerHTML = content;
    
    messageDiv.appendChild(contentDiv);
    messagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Show/hide loading indicator
function showLoadingIndicator(show) {
    document.getElementById("loadingIndicator").style.display = show ? "flex" : "none";
    document.getElementById("sendBtn").disabled = show;
    document.getElementById("queryInput").disabled = show;
}

// Show guardrail warnings
function showGuardrailWarnings(warnings) {
    const warningsDiv = document.getElementById("guardrailWarnings");
    warningsDiv.innerHTML = "";
    warnings.forEach(warning => {
        const p = document.createElement("p");
        p.textContent = warning;
        warningsDiv.appendChild(p);
    });
    warningsDiv.style.display = "block";
}

// Hide guardrail warnings
function hideGuardrailWarnings() {
    document.getElementById("guardrailWarnings").style.display = "none";
}

// Handle Enter key in input
function handleKeyPress(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendQuery();
    }
}

// Close modal
function closeModal() {
    document.getElementById("messageModal").style.display = "none";
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement("div");
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem;
        background: #f44336;
        color: white;
        border-radius: 4px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        max-width: 400px;
    `;
    errorDiv.textContent = message;
    document.body.appendChild(errorDiv);
    
    setTimeout(() => {
        errorDiv.remove();
    }, 5000);
}

// System health check
async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log("System Health:", data);
        
        if (!data.collections_available) {
            showError("Warning: No document collections available. Please run ingestion first.");
        }
    } catch (error) {
        console.warn("Health check failed:", error);
    }
}

// Run health check on startup
setTimeout(checkSystemHealth, 1000);

console.log("FinBot Frontend Ready");

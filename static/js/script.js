const form = document.getElementById("chat-form");
const input = document.getElementById("user-input");
const chatBox = document.getElementById("chat-box");

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const question = input.value.trim();
    if (!question) return;

    // Clear the input field immediately
    input.value = "";

    // Append user's question to the chat box
    chatBox.innerHTML += `
        <p class="user">
            <strong></strong> ${question}
        </p>
    `;

    // Send POST request to Flask server
    const response = await fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ question })
    });

    const data = await response.json();

    if (response.ok) {
        // Format the bot's response
        const formattedAnswer = data.answer
            .split("\n")
            .map(paragraph => `<p>${paragraph}</p>`)
            .join("");

        // Append bot's answer to the chat box
        chatBox.innerHTML += `
            <p class="bot">
                <strong></strong> ${formattedAnswer}
            </p>
        `;
    } else {
        chatBox.innerHTML += `
            <p class="bot">
                <strong>Error:</strong> ${data.error}
            </p>
        `;
    }

    chatBox.scrollTop = chatBox.scrollHeight;  // Scroll to bottom
});

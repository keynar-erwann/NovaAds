const form = document.getElementById("search-form");
const input = document.querySelector(".search-form-input");
const chatWindow = document.getElementById("chat-window");

function getSessionId() {
  let id = localStorage.getItem("nova_session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("nova_session_id", id);
  }
  return id;
}

const SESSION_ID = getSessionId();

if (!chatWindow) {
  console.error("#chat-window element not found in the fucking DOM.");
}

window.addEventListener("DOMContentLoaded", () => {
  appendMessage("nova", "Hello, my name is Nova, your AI ad poster generator ! 🎨 Tell me about your product and your target market, and I'll handle the rest I'll research your niche 🔍, analyse market trends 📊, craft the perfect advertising angle 💡, and generate a stunning, high-converting ad poster just for you ! 🚀 Let's create something amazing together !");
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const userInput = input.value.trim();
  if (!userInput) return;

  appendMessage("user", userInput);
  input.value = "";

  const submitBtn = form.querySelector("button[type='submit']");
  submitBtn.disabled = true;

  await fetchNovaResponse(userInput);

  submitBtn.disabled = false;
});

function appendMessage(sender, text) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add(`message-${sender}`);

  const icon = sender === "user" ? "🧑" : "🔮";
  messageDiv.innerHTML = `
    <span class="icon">${icon}</span>
    <span class="message-text">${text}</span>
  `;

  chatWindow.appendChild(messageDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  return messageDiv;
}

function createStreamingBubble() {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message-nova");

  messageDiv.innerHTML = `
    <span class="icon">🔮</span>
    <span class="message-text"></span>
  `;

  chatWindow.appendChild(messageDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  return messageDiv.querySelector(".message-text");
}

function createWorkingIndicator() {
  const workingDiv = document.createElement("div");
  workingDiv.classList.add("message-nova", "working-indicator");

  workingDiv.innerHTML = `
    <span class="icon">🔮</span>
    <span class="message-text" id="working-text">Working</span>
  `;

  chatWindow.appendChild(workingDiv);
  chatWindow.scrollTop = chatWindow.scrollHeight;

  let dotCount = 0;
  const intervalId = setInterval(() => {
    const el = document.getElementById("working-text");
    if (el) {
      dotCount = (dotCount + 1) % 4;
      el.innerText = "Working" + ".".repeat(dotCount);
    } else {
      clearInterval(intervalId);
    }
  }, 500);

  return {
    remove: () => {
      clearInterval(intervalId);
      workingDiv.remove();
    },
  };
}

async function fetchNovaResponse(userInput) {
  const working = createWorkingIndicator();

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: userInput, session_id: SESSION_ID }),
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    working.remove();
    const textEl = createStreamingBubble();

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split("\n");
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const chunk = line.slice(6);

        if (chunk === "__DONE__") {
          await displayGeneratedImage();
          return;
        }

        textEl.textContent += chunk;
        chatWindow.scrollTop = chatWindow.scrollHeight;
      }
    }

    await displayGeneratedImage();

  } catch (err) {
    working.remove();
    appendMessage("nova", "Something went wrong. Try again bro.");
    console.error("fetchNovaResponse error:", err);
  }
}

async function displayGeneratedImage() {
  try {
    const res = await fetch(`/image?session_id=${SESSION_ID}`);
    if (!res.ok) return;

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);

    const imageDiv = document.createElement("div");
    imageDiv.classList.add("message-nova", "message-image");
    imageDiv.innerHTML = `
      <span class="icon">🔮</span>
      <span class="message-text">
        <img src="${url}" alt="Generated ad poster" class="ad-poster" />
        <a href="${url}" download="nova-ad-poster.png" class="download-btn">⬇ Download Poster</a>
      </span>
    `;

    chatWindow.appendChild(imageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  } catch (err) {
    console.error("displayGeneratedImage error:", err);
  }
}
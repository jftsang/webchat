export class ChatClient {
  constructor(divNode, host = "https://example.com:8000") {
    this.divNode = divNode;
    this.chatForm = this.divNode.querySelector("#chatForm");
    this.chatForm.addEventListener("submit", this.sendMessage);

    this.authorInput = this.divNode.querySelector("#messageAuthor");
    this.authorInput.value = localStorage.getItem("author") || "";
    this.authorInput.addEventListener("input", (event) => {
      localStorage.setItem("author", this.authorInput.value);
    })

    this.messageInput = this.divNode.querySelector("#messageText");
    this.messagesArea = this.divNode.querySelector("#messages");

    const wsUrl = new URL(host);
    wsUrl.protocol = "ws";
    wsUrl.pathname = "/ws";
    this.ws = new WebSocket(wsUrl.toString());
    this.ws.addEventListener("message", this.receiveMessage);
    this.ws.addEventListener("close", () => {
      alert("WebSocket connection closed");
      this.chatForm.querySelector("fieldset").disabled = true;
    })

    const historyUrl = new URL(host);
    historyUrl.pathname = "/history";
    fetch(historyUrl.toString()).then(response => response.json()).then(messages => {
      for (const message of messages) {
        this.displayMessage(message);
      }
    })
  }

  receiveMessage = event => {
    const message = JSON.parse(event.data)
    this.displayMessage(message);
  };

  displayMessage = message => {
    const timestamp = new Date(message.timestamp).toLocaleTimeString();
    const content = `[${timestamp}] ${message.author}: ${message.message}\n`;
    this.messagesArea.textContent += content;
    this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
  };

  sendMessage = event => {
    const data = {
      "author": this.authorInput.value, "message": this.messageInput.value
    };
    this.ws.send(JSON.stringify(data));
    this.messageInput.value = "";
    event.preventDefault();
    this.messageInput.click();
  };
};

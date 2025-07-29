import { useState } from 'react';
import './App.css'
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import InputBox from './components/InputBox';

function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi there! How can I help you today?", time: "06:10 AM" },
  ]);
  const [input, setInput] = useState("");

  const sendMessage = async () => {
    if (!input.trim()) return;

    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    // Push user message immediately to UI
    const updatedMessages = [...messages, { from: "user", text: input, time }];
    setMessages(updatedMessages);
    setInput("");

    try {
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();

      if (data.response) {
        setMessages((prev) => [
          ...updatedMessages,
          { from: "bot", text: data.response, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) },
        ]);
      } else {
        setMessages((prev) => [
          ...updatedMessages,
          { from: "bot", text: "Something went wrong.", time: time },
        ]);
      }
    } catch (err) {
      console.error("API error:", err);
      setMessages((prev) => [
        ...updatedMessages,
        { from: "bot", text: "API request failed.", time: time },
      ]);
    }
  };

  // console.log(input, "input")
  return (
    <>
      <div className="flex h-screen bg-[#0f0f1a] text-white font-sans">
        <Sidebar />
        <div className="flex flex-col flex-1 relative">
          <Header messageCount={messages.length} />
          <div className="flex-1 p-6 overflow-y-auto space-y-4 bg-[#1c1c2e]">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-xs px-4 py-2 rounded-xl ${msg.from === "user"
                    ? " bg-gray-700 text-white"
                    : "bg-gray-700 text-white"
                    }`}
                >
                  {msg.text}
                  <div className="text-xs mt-1 text-gray-300 text-right">{msg.time}</div>
                </div>
              </div>
            ))}
          </div>
          <InputBox input={input} setInput={setInput} sendMessage={sendMessage} />
        </div>

      </div>
    </>
  )
}

export default App

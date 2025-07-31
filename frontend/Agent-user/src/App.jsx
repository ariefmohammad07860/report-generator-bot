import { useEffect, useRef, useState } from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import Header from "./components/Header";
import InputBox from "./components/InputBox";

function App() {
  const [messages, setMessages] = useState([
    { from: "bot", text: "Hi there! How can I help you today?", time: getTime() },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  function getTime() {
    return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userTime = getTime();
    const userMessage = { from: "user", text: input, time: userTime };
    const loadingMessage = { from: "bot", isLoader: true, time: getTime() };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: input }),
      });

      const data = await response.json();
      setIsLoading(false);

      setMessages((prev) => [
        ...prev.slice(0, -1), // remove loader
        {
          from: "bot",
          text: data.response || "Something went wrong.",
          time: getTime(),
        },
      ]);
    } catch (err) {
      console.error("API error:", err);
      setIsLoading(false);

      setMessages((prev) => [
        ...prev.slice(0, -1), // remove loader
        {
          from: "bot",
          text: "API request failed.",
          time: getTime(),
        },
      ]);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
                <div className="max-w-xs px-4 py-2 rounded-xl bg-gray-700 text-white">
                  {msg.isLoader ? (
                    <div className="loader mx-auto my-1">
                      <div></div>
                      <div></div>
                      <div></div>
                    </div>
                  ) : (
                    <>
                      {msg.text}
                      <div className="text-xs mt-1 text-gray-300 text-right">{msg.time}</div>
                    </>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
          <InputBox input={input} setInput={setInput} sendMessage={sendMessage} />
        </div>
      </div>
    </>
  );
}

export default App;

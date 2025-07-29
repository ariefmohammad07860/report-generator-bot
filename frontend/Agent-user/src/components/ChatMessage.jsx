const ChatMessage = ({ msg }) => (
  <div className={`flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}>
    <div className={`max-w-xs px-4 py-2 rounded-xl ${
      msg.from === "user"
        ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white"
        : "bg-gray-700 text-white"
    }`}>
      {msg.text}
      <div className="text-xs mt-1 text-gray-300 text-right">{msg.time}</div>
    </div>
  </div>
);

export default ChatMessage;

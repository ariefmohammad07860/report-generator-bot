import React from "react";

const InputBox = ({ input, setInput, sendMessage }) => {
  return (
    <div className="p-4 border-t border-gray-800 bg-[#151527]">
      <div className="flex items-center space-x-2">
        <input
          type="text"
          className="flex-1 px-4 py-2 rounded-lg bg-gray-800 text-white outline-none"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button
          onClick={sendMessage}
          className=" bg-blue-300 px-4 py-2 rounded-lg text-white font-medium cursor-pointer"
        >
          ➤
        </button>
      </div>
    </div>
  );
};

export default InputBox;

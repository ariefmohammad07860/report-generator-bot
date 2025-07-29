import React from "react";

const Sidebar = () => {
  return (
    <div className="w-64 bg-[#151527] border-r border-gray-800 p-4">
      <h2 className="text-xl font-semibold mb-4 text-white">Chat History</h2>
      <button className="bg-gradient-to-r from-pink-500 to-purple-500 w-full py-2 rounded-md text-white font-medium">
        + New Chat
      </button>
      <div className="mt-6 text-gray-400">
        New Chat<br />
        <small>Today · 0 messages</small>
      </div>
    </div>
  );
};

export default Sidebar;

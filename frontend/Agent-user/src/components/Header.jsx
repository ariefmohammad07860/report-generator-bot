import React from "react";

const Header = ({ messageCount }) => {
  // console.log(messageCount)
  return (
    <div className=" bg-blue-300 p-4 shadow-lg">
      <h1 className="text-xl font-bold text-white">AI Assistant ✨</h1>
      <p className="text-sm text-white">{messageCount} messages exchanged</p>
    </div>
  );
};

export default Header;

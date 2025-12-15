// src/components/LogoutButton.jsx
import React from "react";
import { useAuth } from "../context/AuthContext";

export default function LogoutButton({ className = "" }) {
  const { logout } = useAuth();
  return (
    <button
      onClick={logout}
      className={`px-3 py-1 rounded bg-red-500 hover:bg-red-600 text-white ${className}`}
    >
      Logout
    </button>
  );
}

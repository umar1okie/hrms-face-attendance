// src/components/Navbar.jsx
import React from "react";
import { Link } from "react-router-dom";
import LogoutButton from "./LogoutButton";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user } = useAuth();
  return (
    <nav className="fixed top-0 left-0 right-0 bg-white shadow z-40">
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center gap-4">
        <Link to="/dashboard" className="font-semibold text-lg">Dashboard</Link>

        <div className="flex-1" />

        <Link to="/check-in" className="px-3 py-1 rounded hover:bg-gray-100">Check-in</Link>
        <Link to="/face-registration" className="px-3 py-1 rounded hover:bg-gray-100">Face Reg</Link>
        {user?.is_admin && (<Link to="/admin-review" className="px-3 py-1 rounded hover:bg-gray-100">Admin Review</Link>)}
        <Link to="/CompleteProfile" className="px-3 py-1 rounded hover:bg-gray-100">CompleteProfile</Link>

        <div className="ml-4 text-sm text-gray-600">
          {user?.username ?? "Guest"}
        </div>

        <LogoutButton className="ml-4" />
      </div>
    </nav>
  );
}

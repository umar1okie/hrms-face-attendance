// src/pages/Login.jsx
import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { loginUser } from "../services/api";

export default function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      const data = await loginUser(username, password);

      // Save tokens + user in auth context
      login({
        access: data.access,
        refresh: data.refresh,
        user: {
          username: data.username,
          id: data.employee_id,
          department: data.department,
          designation: data.designation,
          is_admin: data.is_admin, // ✅ ADDED
        },
      });

      // Save locally (for dashboard UI)
      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);
      localStorage.setItem("username", data.username);
      localStorage.setItem("employee_id", data.employee_id);
      localStorage.setItem("department", data.department || "");
      localStorage.setItem("designation", data.designation || "");


      if (data.is_admin) {
        navigate("/admin-review");
        return;
      }

      // ✅ EMPLOYEE FLOW (UNCHANGED)
      if (!data.department || !data.designation) {
        navigate("/complete-profile");
      } else {
        navigate("/dashboard");
      }

    } catch (err) {
      setError("❌ Incorrect username or password.");
    }
  };

  return (
    <div className="flex items-center justify-center h-screen bg-gray-100">
      <form
        onSubmit={handleSubmit}
        className="bg-white p-8 rounded-xl shadow-lg w-full max-w-sm"
      >
        <h2 className="text-2xl font-bold text-center mb-6">Login</h2>

        {error && (
          <p className="bg-red-100 text-red-600 p-2 rounded mb-3 text-center">
            {error}
          </p>
        )}

        <label className="block mb-2 font-medium">Username</label>
        <input
          type="text"
          className="w-full p-2 border rounded mb-4"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />

        <label className="block mb-2 font-medium">Password</label>
        <input
          type="password"
          className="w-full p-2 border rounded mb-4"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition"
        >
          Login
        </button>

        <p className="text-center mt-4 text-sm">
          Not registered?{" "}
          <Link to="/register" className="text-blue-600 underline">
            Create an account
          </Link>
        </p>
      </form>
    </div>
  );
}

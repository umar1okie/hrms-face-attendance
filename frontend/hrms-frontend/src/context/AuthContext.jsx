// src/context/AuthContext.jsx
import React, { createContext, useContext, useEffect, useState } from "react";
import { decodeJwtPayload } from "../utils/jwt";

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  // Restore session from localStorage
  useEffect(() => {
    const access = localStorage.getItem("access_token");
    const storedUser = localStorage.getItem("user");

    if (access && storedUser) {
      const payload = decodeJwtPayload(access);
      const parsedUser = JSON.parse(storedUser);

      setUser({
        ...parsedUser,
        exp: payload?.exp,
      });
    }

    setReady(true);
  }, []);

  // LOGIN
  const login = ({ access, refresh, user }) => {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);

    // 🔑 STORE FULL USER (INCLUDING is_admin)
    localStorage.setItem("user", JSON.stringify(user));

    setUser(user);
  };

  // LOGOUT
  const logout = () => {
    localStorage.clear();
    setUser(null);
    window.location.href = "/login";
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, ready }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);

// src/App.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";

import Login from "./pages/Login";
import Register from "./pages/Register";
import EmployeeDashboard from "./pages/EmployeeDashboard";
import DailyCheckIn from "./pages/DailyCheckIn";
import FaceRegistration from "./pages/FaceRegistration";
import AdminReview from "./pages/AdminReview";
import Navbar from "./components/Navbar";
import ProtectedRoute from "./components/ProtectedRoute";
import CompleteProfile from "./pages/CompleteProfile"
import AdminRoute from "./components/AdminRoute";


export default function App(){
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login/>}/>
          <Route path="/register" element={<Register/>}/>
          <Route path="/face-registration" element={<ProtectedRoute><Navbar/><FaceRegistration/></ProtectedRoute>}/>
          <Route path="/dashboard" element={<ProtectedRoute><Navbar/><EmployeeDashboard/></ProtectedRoute>} />
          <Route path="/check-in" element={<ProtectedRoute><Navbar/><DailyCheckIn/></ProtectedRoute>} />
          <Route path="/admin-review" element={<AdminRoute><Navbar /><AdminReview /></AdminRoute>}/>
          <Route path="/complete-profile" element={<ProtectedRoute><Navbar/><CompleteProfile /></ProtectedRoute>} />
          <Route path="*" element={<Login/>}/>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

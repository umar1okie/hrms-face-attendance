import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProfileStatus, updateProfile } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function CompleteProfile() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [loading, setLoading] = useState(true);
  const [department, setDepartment] = useState("");
  const [designation, setDesignation] = useState("");
  const [isRemote, setIsRemote] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const data = await getProfileStatus();
        if (!mounted) return;
        // if already complete → go to face registration
        if (data.profile_complete) {
          navigate("/face-registration");
          return;
        }
        setDepartment(data.department || "");
        setDesignation(data.designation || "");
      } catch (err) {
        setError("Unable to fetch profile status. Make sure you are logged in.");
      } finally {
        setLoading(false);
      }
    })();
    return () => (mounted = false);
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!department || !designation) {
      setError("Department and designation are required.");
      return;
    }
    try {
      await updateProfile({ department, designation, is_remote_worker: isRemote });
      // update localStorage so Dashboard shows correct values
      localStorage.setItem("department", department);
      localStorage.setItem("designation", designation);
      navigate("/face-registration");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to update profile");
    }
  };

  if (loading) return <div className="p-6">Loading...</div>;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Complete your profile</h2>
        <p className="text-sm text-gray-600 mb-4">Before face registration we need a couple of details.</p>

        {error && <div className="bg-red-100 text-red-700 p-2 rounded mb-3">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Department</label>
            <input
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="mt-1 w-full px-3 py-2 border rounded"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium">Designation</label>
            <input
              value={designation}
              onChange={(e) => setDesignation(e.target.value)}
              className="mt-1 w-full px-3 py-2 border rounded"
              required
            />
          </div>

          <div className="flex items-center space-x-2">
            <input
              id="remote"
              type="checkbox"
              checked={isRemote}
              onChange={(e) => setIsRemote(e.target.checked)}
            />
            <label htmlFor="remote" className="text-sm">
              Remote worker
            </label>
          </div>

          <button className="w-full bg-indigo-600 text-white py-2 rounded">
            Save & Continue
          </button>
        </form>
      </div>
    </div>
  );
}

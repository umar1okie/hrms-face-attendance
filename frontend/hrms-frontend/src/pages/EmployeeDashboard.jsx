// src/pages/EmployeeDashboard.jsx
import React, { useEffect, useState } from "react";
import Navbar from "../components/Navbar";
import { Link } from "react-router-dom";
import { getAttendanceHistory } from "../services/api";

export default function EmployeeDashboard() {
  const username = localStorage.getItem("username") || "";
  const employeeId = localStorage.getItem("employee_id") || "-";

  const [history, setHistory] = useState([]);
  const [todayStatus, setTodayStatus] = useState("Not Checked In");
  const [todayCheckIn, setTodayCheckIn] = useState(null);
  const [todayCheckOut, setTodayCheckOut] = useState(null);
  const [workDuration, setWorkDuration] = useState("00:00:00");

  const [filterDate, setFilterDate] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");

  // Load history
  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await getAttendanceHistory();
        setHistory(res);

        // Today's record detection
        const today = new Date().toISOString().slice(0, 10);
        const todayRecord = res.find(r => r.check_in_time.startsWith(today));

        if (todayRecord) {
          setTodayCheckIn(todayRecord.check_in_time);
          setTodayCheckOut(todayRecord.check_out_time);
          setTodayStatus(todayRecord.check_out_time ? "Checked Out" : "Checked In");
        }
      } catch (err) {
        console.log("History load failed:", err);
      }
    }

    loadHistory();
  }, []);

  // Auto-update work duration timer
  useEffect(() => {
    if (!todayCheckIn || todayCheckOut) return;

    const interval = setInterval(() => {
      const start = new Date(todayCheckIn);
      const now = new Date();
      const diff = Math.floor((now - start) / 1000);

      const hrs = String(Math.floor(diff / 3600)).padStart(2, "0");
      const mins = String(Math.floor((diff % 3600) / 60)).padStart(2, "0");
      const secs = String(diff % 60).padStart(2, "0");

      setWorkDuration(`${hrs}:${mins}:${secs}`);
    }, 1000);

    return () => clearInterval(interval);
  }, [todayCheckIn, todayCheckOut]);

  // Monthly Stats
  const daysPresent = history.length;
  const totalWorkHours = history.reduce((sum, item) => {
    if (!item.check_out_time) return sum;
    const s = new Date(item.check_in_time);
    const e = new Date(item.check_out_time);
    return sum + (e - s) / 3600000;
  }, 0).toFixed(2);

  // History filtering
  const filteredHistory = history.filter((h) => {
    const dateMatch = filterDate ? h.check_in_time.startsWith(filterDate) : true;
    const statusMatch =
      filterStatus === "checked_in"
        ? !h.check_out_time
        : filterStatus === "checked_out"
        ? h.check_out_time
        : true;

    return dateMatch && statusMatch;
  });

  return (
    <>
      <Navbar />

      <div className="pt-20 max-w-6xl mx-auto p-6">
        <h1 className="text-2xl font-semibold mb-4">Employee Dashboard</h1>

        {/* TOP GRID */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* PROFILE CARD */}
          <div className="bg-white rounded-xl shadow p-4">
            <h3 className="font-medium text-gray-700">Profile</h3>
            <p className="text-sm text-gray-600 mt-2">
              Username: <strong>{username}</strong>
            </p>
            <p className="text-sm text-gray-600 mt-1">
              Employee ID: <strong>{employeeId}</strong>
            </p>
          </div>

          {/* TODAY STATUS CARD */}
          <div className="bg-white rounded-xl shadow p-4 col-span-2">
            <h3 className="font-medium text-gray-700">Today's Status</h3>

            <p className="mt-3 text-sm">
              Status:{" "}
              <strong className={todayStatus === "Checked In" ? "text-green-600" : "text-red-600"}>
                {todayStatus}
              </strong>
            </p>

            <p className="text-sm mt-2">
              Check-in:{" "}
              {todayCheckIn ? new Date(todayCheckIn).toLocaleTimeString() : "--"}
            </p>

            <p className="text-sm">
              Check-out:{" "}
              {todayCheckOut ? new Date(todayCheckOut).toLocaleTimeString() : "--"}
            </p>

            <p className="text-sm mt-2">
              Current Work Duration:{" "}
              <strong className="text-indigo-600">{workDuration}</strong>
            </p>

            <div className="mt-4 flex gap-3">
              <Link
                to="/check-in"
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
              >
                Check-in / Check-out
              </Link>

              <Link
                to="/face-registration"
                className="px-4 py-2 border rounded hover:bg-gray-100"
              >
                Register Face
              </Link>
            </div>
          </div>
        </div>

        {/* MONTHLY SUMMARY */}
        <div className="mt-6 bg-white rounded-xl shadow p-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <h3 className="font-medium text-gray-700">Days Present</h3>
            <p className="text-3xl mt-2">{daysPresent}</p>
          </div>

          <div>
            <h3 className="font-medium text-gray-700">Total Work Hours</h3>
            <p className="text-3xl mt-2">{totalWorkHours} hrs</p>
          </div>

          <div>
            <h3 className="font-medium text-gray-700">Average Work/Day</h3>
            <p className="text-3xl mt-2">
              {daysPresent > 0 ? (totalWorkHours / daysPresent).toFixed(2) : 0} hrs
            </p>
          </div>
        </div>

        {/* HISTORY WITH FILTERS */}
        <div className="mt-6 bg-white rounded-xl shadow p-4">
          <h3 className="font-medium text-gray-700">History</h3>

          {/* FILTERS */}
          <div className="flex gap-4 mt-4">
            <input
              type="date"
              className="border rounded px-2 py-1"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
            />

            <select
              className="border rounded px-2 py-1"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All</option>
              <option value="checked_in">Not Checked Out</option>
              <option value="checked_out">Checked Out</option>
            </select>
          </div>

          {/* HISTORY LIST */}
          <div className="mt-4">
            {filteredHistory.length === 0 ? (
              <p className="text-sm text-gray-600">No records found.</p>
            ) : (
              filteredHistory.map((h, i) => (
                <div key={i} className="border-b py-2 text-sm">
                  <strong>{new Date(h.check_in_time).toLocaleString()}</strong>
                  {h.check_out_time ? (
                    <> — Checked out at {new Date(h.check_out_time).toLocaleTimeString()}</>
                  ) : (
                    <> — Not checked out</>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </>
  );
}

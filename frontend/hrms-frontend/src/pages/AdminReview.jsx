import React, { useEffect, useMemo, useState, useRef } from "react";

import Navbar from "../components/Navbar";
import api from "../services/api";

export default function AdminReview() {
  const socketRef = useRef(null);


  const [pending, setPending] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [notes, setNotes] = useState({});
  const [filters, setFilters] = useState({
    employee: "",
    minConfidence: "",
    date: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /* -------------------- LOAD DATA -------------------- */
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [pendingRes, anomalyRes] = await Promise.all([
          api.get("review/pending/"),
          api.get("review/anomalies/"),
        ]);

        setPending(pendingRes.data || []);
        setAnomalies(anomalyRes.data || []);
      } catch (err) {
        setError("Failed to load admin review data");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  /* -------------------- WEBSOCKET (REAL-TIME) -------------------- */
useEffect(() => {
  const token = localStorage.getItem("access_token"); // MUST exist
  if (!token) return;

  const socket = new WebSocket(
    `ws://127.0.0.1:8000/ws/admin/?token=${token}`
  );

  socketRef.current = socket;

  socket.onopen = () => {
    console.log("✅ Admin WebSocket connected");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.event === "attendance.pending") {
      setPending((prev) => [data.payload, ...prev]);
    }

    if (data.event === "attendance.updated") {
      setPending((prev) =>
        prev.filter((p) => p.employee_id !== data.employee_id)
      );
    }

    if (data.event === "anomaly.created") {
      setAnomalies((prev) => [data.payload, ...prev]);
    }
  };

  socket.onerror = (err) => {
    console.error("❌ WebSocket error", err);
  };

  socket.onclose = () => {
    console.log("⚠️ Admin WebSocket closed");
  };

  return () => socket.close();
}, []);



  /* -------------------- FILTERING -------------------- */
  const filtered = useMemo(() => {
    return pending.filter((p) => {
      if (filters.employee && !p.employee_id.includes(filters.employee)) return false;
      if (filters.minConfidence && p.confidence_score < Number(filters.minConfidence)) return false;
      if (filters.date && !p.check_in_time.startsWith(filters.date)) return false;
      return true;
    });
  }, [pending, filters]);

  /* -------------------- ACTIONS -------------------- */
  const approve = async (employee_id) => {
    await api.post("review/approve/", {
      employee_id,
      notes: notes[employee_id] || "",
    });
    setPending((p) => p.filter((x) => x.employee_id !== employee_id));
  };

  const reject = async (employee_id) => {
    await api.post("review/reject/", {
      employee_id,
      notes: notes[employee_id] || "",
    });
    setPending((p) => p.filter((x) => x.employee_id !== employee_id));
  };

  const toggleSelect = (employee_id) => {
    setSelected((prev) => {
      const s = new Set(prev);
      s.has(employee_id) ? s.delete(employee_id) : s.add(employee_id);
      return s;
    });
  };

  const batchApprove = async () => {
    await api.post("review/batch-approve/", {
      ids: Array.from(selected), // backend expects IDs
    });
    setPending((p) => p.filter((x) => !selected.has(x.employee_id)));
    setSelected(new Set());
  };

  /* -------------------- UI -------------------- */
  return (
    <>
      <Navbar />
      <div className="pt-20 max-w-7xl mx-auto p-6 space-y-6">
        <h2 className="text-2xl font-semibold">Admin Attendance Review</h2>

        {loading && <div>Loading...</div>}
        {error && <div className="text-red-600">{error}</div>}

        {/* FILTERS */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 bg-white p-4 rounded shadow">
          <input
            placeholder="Employee ID"
            className="border p-2 rounded"
            onChange={(e) => setFilters({ ...filters, employee: e.target.value })}
          />
          <input
            placeholder="Min confidence"
            type="number"
            step="0.01"
            className="border p-2 rounded"
            onChange={(e) => setFilters({ ...filters, minConfidence: e.target.value })}
          />
          <input
            type="date"
            className="border p-2 rounded"
            onChange={(e) => setFilters({ ...filters, date: e.target.value })}
          />
          <button
            onClick={batchApprove}
            disabled={!selected.size}
            className="bg-green-600 text-white rounded px-3 disabled:opacity-50"
          >
            Batch Approve
          </button>
        </div>

        {/* PENDING QUEUE */}
        <div className="space-y-4">
          {filtered.map((it) => (
            <div
              key={it.id}
              className="bg-white rounded shadow p-4 grid grid-cols-1 md:grid-cols-6 gap-4"
            >
              {/* SELECT */}
              <input
                type="checkbox"
                checked={selected.has(it.employee_id)}
                onChange={() => toggleSelect(it.employee_id)}
              />

              {/* SIDE-BY-SIDE IMAGE */}
              <img
                src={it.image_url}
                alt="verification"
                className="h-32 w-32 object-cover rounded border"
              />

              {/* INFO */}
              <div className="md:col-span-2">
                <div className="font-medium">
                  {it.employee_name} ({it.employee_id})
                </div>
                <div className="text-sm text-gray-600">
                  {new Date(it.check_in_time).toLocaleString()}
                </div>

                {/* CONFIDENCE BAR */}
                <div className="mt-3">
                  <div className="text-xs">Confidence</div>
                  <div className="w-full bg-gray-200 rounded h-2">
                    <div
                      className="bg-blue-600 h-2 rounded"
                      style={{ width: `${it.confidence_score * 100}%` }}
                    />
                  </div>
                  <div className="text-xs mt-1">
                    {(it.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* NOTES + ACTIONS */}
              <div className="md:col-span-2 space-y-2">
                <textarea
                  placeholder="Admin notes"
                  className="border w-full p-2 rounded text-sm"
                  onChange={(e) =>
                    setNotes({ ...notes, [it.employee_id]: e.target.value })
                  }
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => approve(it.employee_id)}
                    className="flex-1 bg-green-600 text-white rounded px-2 py-1"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => reject(it.employee_id)}
                    className="flex-1 bg-red-500 text-white rounded px-2 py-1"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* ANOMALIES */}
        <div className="bg-white rounded shadow p-4">
          <h3 className="font-semibold mb-2">Anomaly Alerts</h3>
          {anomalies.length === 0 && (
            <div className="text-sm text-gray-600">No anomalies detected</div>
          )}
          {anomalies.map((a) => (
            <div key={a.id} className="border-b py-2 text-sm">
              <span className="font-medium">{a.employee_name}</span> —{" "}
              {a.type} ({a.severity})
            </div>
          ))}
        </div>
      </div>
    </>
  );
}

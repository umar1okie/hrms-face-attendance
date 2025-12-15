// src/pages/FaceRegistration.jsx
import React, { useRef, useState } from "react";
import Webcam from "react-webcam";
import { registerFace } from "../services/api";
import Navbar from "../components/Navbar";

const videoConstraints = { width: 640, height: 480, facingMode: "user" };

export default function FaceRegistration() {
  const webcamRef = useRef(null);
  const [isCameraOn, setIsCameraOn] = useState(false);
  const [capturedBlobs, setCapturedBlobs] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [consent, setConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const startCamera = () => setIsCameraOn(true);
  const stopCamera = () => {
    const s = webcamRef.current?.stream;
    if (s) s.getTracks().forEach((t) => t.stop());
    setIsCameraOn(false);
  };

  const capturePhoto = () => {
    const dataUrl = webcamRef.current?.getScreenshot();
    if (!dataUrl) return;
    const blob = dataURLToBlob(dataUrl);
    setCapturedBlobs((p) => (p.length >= 5 ? p : [...p, blob]));
    if (selectedIndex === null) setSelectedIndex(0);
  };

  const dataURLToBlob = (dataurl) => {
    const [header, base64] = dataurl.split(",");
    const mime = header.match(/:(.*?);/)[1];
    const binary = atob(base64);
    const array = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) array[i] = binary.charCodeAt(i);
    return new Blob([array], { type: mime });
  };

  const upload = async () => {
    if (!consent) return setMessage({ type: "error", text: "Give consent." });
    if (capturedBlobs.length === 0) return setMessage({ type: "error", text: "Capture at least one photo." });

    setLoading(true);
    setMessage(null);

    try {
      const idx = selectedIndex ?? 0;
      const fd = new FormData();

      // optional: if you saved user data locally during register, include them
      const username = localStorage.getItem("username") || "";
      const employee_id = localStorage.getItem("employee_id") || "";

      if (username) fd.append("username", username);
      if (employee_id) fd.append("employee_id", employee_id);

      fd.append("image", capturedBlobs[idx], "capture.jpg");

      const res = await registerFace(fd);
      setMessage({ type: "success", text: res.message || "Registered." });
      setCapturedBlobs([]);
      setSelectedIndex(null);
      stopCamera();
    } catch (err) {
      const m = err.response?.data || err.message;
      setMessage({ type: "error", text: JSON.stringify(m) });
    } finally {
      setLoading(false);
    }
  };

  const remove = (i) => {
    setCapturedBlobs((p) => p.filter((_, idx) => idx !== i));
    if (selectedIndex === i) setSelectedIndex(null);
    else if (selectedIndex > i) setSelectedIndex((s) => s - 1);
  };

  return (
    <>
      <Navbar />
      <div className="pt-20 max-w-4xl mx-auto p-6">
        <h2 className="text-2xl font-semibold mb-4">Face Registration</h2>

        <div className="bg-gray-50 p-4 rounded border mb-4">
          <h3 className="font-medium">Privacy & consent</h3>
          <p className="text-sm text-gray-600 mt-1">
            Captured images are used for attendance only.
          </p>
          <label className="inline-flex items-center mt-3">
            <input type="checkbox" className="mr-2" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            I give consent.
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="bg-black p-2 rounded">
              {isCameraOn ? (
                <Webcam
                  audio={false}
                  ref={webcamRef}
                  screenshotFormat="image/jpeg"
                  videoConstraints={videoConstraints}
                  className="w-full rounded"
                />
              ) : (
                <div className="w-full h-64 flex items-center justify-center text-gray-400 bg-gray-100 rounded">
                  Camera is off
                </div>
              )}
            </div>

            <div className="mt-3 flex gap-2">
              {!isCameraOn ? (
                <button onClick={startCamera} className="px-4 py-2 bg-blue-600 text-white rounded">Allow Camera</button>
              ) : (
                <>
                  <button onClick={capturePhoto} className="px-4 py-2 bg-green-600 text-white rounded">Capture</button>
                  <button onClick={stopCamera} className="px-4 py-2 bg-red-500 text-white rounded">Stop</button>
                </>
              )}
              <div className="ml-auto text-sm text-gray-500">{capturedBlobs.length}/5</div>
            </div>
          </div>

          <div>
            <div className="space-y-3">
              <p className="text-sm text-gray-600">Tip: good lighting & multiple angles help recognition.</p>
              <div>
                <label className="text-sm">Selected capture</label>
                {selectedIndex !== null ? (
                  <img src={URL.createObjectURL(capturedBlobs[selectedIndex])} alt="sel" className="w-full rounded mt-2" />
                ) : (
                  <div className="w-full h-32 bg-gray-100 rounded flex items-center justify-center mt-2 text-sm">No selection</div>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="mt-6">
          <h4 className="font-medium mb-2">Captured Photos</h4>
          <div className="flex gap-3 overflow-x-auto">
            {capturedBlobs.length === 0 && <div className="text-sm text-gray-500">No captures yet</div>}
            {capturedBlobs.map((b, i) => (
              <div key={i} className="flex flex-col items-center">
                <img
                  src={URL.createObjectURL(b)}
                  alt={"capture-" + i}
                  className={`w-36 h-28 object-cover rounded ${selectedIndex === i ? "ring-4 ring-blue-400" : ""}`}
                  onClick={() => setSelectedIndex(i)}
                />
                <div className="flex gap-1 mt-1">
                  <button onClick={() => setSelectedIndex(i)} className="px-2 py-1 text-xs bg-blue-600 text-white rounded">Select</button>
                  <button onClick={() => remove(i)} className="px-2 py-1 text-xs bg-red-500 text-white rounded">Remove</button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-6 flex gap-3">
          <button onClick={upload} disabled={loading} className="px-4 py-2 bg-indigo-600 text-white rounded">
            {loading ? "Uploading..." : "Register Face"}
          </button>
          <button onClick={() => { setCapturedBlobs([]); setSelectedIndex(null); setMessage(null); }} className="px-4 py-2 border rounded">Reset</button>
        </div>

        {message && (
          <div className={`mt-4 p-3 rounded ${message.type === "success" ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>
            {message.text}
          </div>
        )}
      </div>
    </>
  );
}

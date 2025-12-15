// src/pages/DailyCheckIn.jsx
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar";
import { checkIn, checkOut } from "../services/api";

export default function DailyCheckIn() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const timerRef = useRef(null);
  const navigate = useNavigate();

  // User info
  const username = localStorage.getItem("username") || "";
  const employeeId = localStorage.getItem("employee_id") || "";
  const department = localStorage.getItem("department") || "";
  const designation = localStorage.getItem("designation") || "";

  // UI states
  const [capturedImage, setCapturedImage] = useState(null);
  const [statusMsg, setStatusMsg] = useState("");
  const [confidence, setConfidence] = useState(null);
  const [loading, setLoading] = useState(false);

  // Camera on/off
  const [cameraOn, setCameraOn] = useState(false);

  const pushToast = (msg) => alert(msg);

  // -------------------------------
  // RESTORE STATE ON PAGE LOAD
  // -------------------------------
  useEffect(() => {
    const savedImage = localStorage.getItem("capturedImage");
    // const savedStartTime = localStorage.getItem("checkInStartTime");
    const savedStatus = localStorage.getItem("statusMsg");

    if (savedImage) setCapturedImage(savedImage);
    if (savedStatus) setStatusMsg(savedStatus);

    return () => stopCamera();
  }, []);

  // -------------------------------
  // FIXED CAMERA START FUNCTION
  // -------------------------------
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        // IMPORTANT FIX: ensures instant camera start
        await videoRef.current.play().catch(() => {});

        setCameraOn(true);
      }
    } catch (err) {
      console.error("Camera error:", err);
      pushToast("Unable to access camera");
    }
  };

  // Stop camera
  const stopCamera = () => {
    const video = videoRef.current;
    const stream = video?.srcObject;

    if (stream) stream.getTracks().forEach((t) => t.stop());

    if (video) {
      video.pause();
      video.srcObject = null;
    }

    setCameraOn(false);
  };

  // -------------------------------
  // CAPTURE PHOTO (PERSIST IN STORAGE)
  // -------------------------------
  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;

    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const img = canvas.toDataURL("image/jpeg");
    setCapturedImage(img);

    localStorage.setItem("capturedImage", img);
  };

  // -------------------------------
  // CHECK-IN
  // -------------------------------
  const handleCheckIn = async () => {
    if (loading) return;
    setLoading(true);
    setStatusMsg("");

    if (!capturedImage) {
      pushToast("Please capture a photo first");
      setLoading(false);
      return;
    }

    try {
      const formData = new FormData();
      formData.append("image", dataURLtoFile(capturedImage, "attendance.jpg"));

      const resp = await checkIn(formData);

      setStatusMsg("Checked In Successfully!");
      localStorage.setItem("statusMsg", "Checked In Successfully!");

      setConfidence(resp.confidence_score || 0);
    } catch (err) {
      console.error("CHECK-IN ERROR:", err);
      pushToast("Face not recognized or server error");
    } finally {
      setLoading(false);
    }
  };

  // -------------------------------
  // CHECK-OUT
  // -------------------------------
  const handleCheckOut = async () => {
    if (loading) return;
    setLoading(true);

    try {
      await checkOut(employeeId);

      setStatusMsg("Checked Out");

      pushToast("Checked out successfully!");

      localStorage.removeItem("capturedImage");
      localStorage.removeItem("checkInStartTime");
      localStorage.removeItem("statusMsg");

      setCapturedImage(null);
    } catch (err) {
      console.error("CHECK-OUT ERROR:", err);
      pushToast("Checkout failed");
    } finally {
      setLoading(false);
    }
  };

  // Base64 → File
  const dataURLtoFile = (dataUrl, filename) => {
    const arr = dataUrl.split(",");
    const mime = arr[0].match(/:(.*?);/)[1];
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) u8arr[n] = bstr.charCodeAt(n);
    return new File([u8arr], filename, { type: mime });
  };

  // -----------------------------------------------------
  // UI
  // -----------------------------------------------------
  return (
    <>
      <Navbar />

      <div className="pt-24 max-w-4xl mx-auto p-6">
        <h1 className="text-2xl font-semibold">Daily Check-In</h1>

        {/* USER INFO */}
        <div className="bg-white p-4 mt-4 rounded-xl shadow">
          <p>
            <strong>Name:</strong> {username}
          </p>
          <p>
            <strong>Employee ID:</strong> {employeeId}
          </p>
          <p>
            <strong>Department:</strong> {department}
          </p>
          <p>
            <strong>Designation:</strong> {designation}
          </p>
        </div>

        {/* CAMERA + IMAGE */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Camera */}
          <div className="bg-white p-4 rounded-xl shadow relative">
            {/* Camera Toggle Button */}
            <button
              onClick={cameraOn ? stopCamera : startCamera}
              className={`absolute top-2 right-2 z-50 px-3 py-1 rounded-lg text-sm text-white
                ${cameraOn ? "bg-red-600 hover:bg-red-700" : "bg-green-600 hover:bg-green-700"}`}>
              {cameraOn ? "Stop Camera" : "Start Camera"}
            </button>

            {/* VIDEO FIX: Add pointer-events-none */}
            <video
              ref={videoRef}
              className="w-full rounded-lg pointer-events-none"
            ></video>

            <button
              onClick={capturePhoto}
              disabled={!cameraOn}
              className={`mt-3 w-full py-2 rounded text-white ${
                cameraOn ? "bg-blue-600 hover:bg-blue-700" : "bg-gray-400"
              }`}
            >
              Capture Photo
            </button>
          </div>

          {/* Captured Image */}
          <div className="bg-white p-4 rounded-xl shadow flex flex-col items-center">
            <canvas ref={canvasRef} className="hidden"></canvas>

            {capturedImage ? (
              <img
                src={capturedImage}
                alt="Captured"
                className="w-full rounded-lg border"
              />
            ) : (
              <p className="text-gray-500">No photo captured</p>
            )}

            <p className="mt-3 text-gray-700">
              Confidence: <strong>{confidence ?? "N/A"}</strong>
            </p>
          </div>
        </div>

        {/* ACTION BUTTONS */}
        <div className="mt-6 flex gap-4">
          <button
            onClick={handleCheckIn}
            disabled={loading}
            className={`px-6 py-2 rounded text-white ${
              loading ? "bg-gray-400" : "bg-green-600"
            }`}
          >
            {loading ? "Processing…" : "Check In"}
          </button>

          <button
            onClick={handleCheckOut}
            disabled={loading}
            className={`px-6 py-2 rounded text-white ${
              loading ? "bg-gray-400" : "bg-red-600"
            }`}
          >
            Check Out
          </button>
        </div>

        {/* STATUS */}
        <div className="mt-4 bg-white p-4 rounded-xl shadow">
          <p>
            <strong>Status:</strong> {statusMsg}
          </p>
        </div>
      </div>
    </>
  );
}

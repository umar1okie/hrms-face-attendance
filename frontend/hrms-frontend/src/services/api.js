import axios from "axios";


const API_BASE = "http://127.0.0.1:8000/api/";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// JWT Helpers
const getAccess = () => localStorage.getItem("access_token");
const getRefresh = () => localStorage.getItem("refresh_token");

// Add token
api.interceptors.request.use((config) => {
  const token = getAccess();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Token Refresh
let isRefreshing = false;
let failedQueue = [];

const processQueue = (err, token = null) => {
  failedQueue.forEach((p) => (err ? p.reject(err) : p.resolve(token)));
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      isRefreshing = true;

      try {
        const refresh = getRefresh();
        if (!refresh) throw new Error("No refresh token");

        // FIXED (removed double slash)
        const resp = await axios.post(`${API_BASE}auth/token/refresh/`, {
          refresh,
        });

        const newAccess = resp.data.access;
        localStorage.setItem("access_token", newAccess);

        api.defaults.headers.common["Authorization"] = `Bearer ${newAccess}`;
        processQueue(null, newAccess);

        return api(originalRequest);
      } catch (err) {
        processQueue(err, null);
        localStorage.clear();
        window.location.href = "/login";
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ------------------------------
// AUTH
// ------------------------------
export const loginUser = async (username, password) => {
  return (await api.post("auth/login/", { username, password })).data;
};

export const registerUser = async (payload) => {
  return (await api.post("auth/register/", payload)).data;
};

// ------------------------------
// FACE REGISTRATION
// ------------------------------
export const registerFace = async (formData) => {
  return (
    await api.post("face/register/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  ).data;
};

// ------------------------------
// CHECK-IN
// ------------------------------
export const checkIn = async (formData) => {
  return (
    await api.post("attendance/checkin/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    })
  ).data;
};

// ------------------------------
// CHECKOUT
// ------------------------------
export const checkOut = async (employee_id) => {
  const id = Array.isArray(employee_id) ? employee_id[0] : employee_id;

  const resp = await api.post("attendance/checkout/", {
    employee_id: String(id).trim(),
  });

  return resp.data;
};


// ------------------------------
// TODAY STATUS
// ------------------------------
export const getTodayStatus = async () => {
  return (await api.get("attendance/today/")).data;
};

// ------------------------------
// HISTORY
// ------------------------------
export const getAttendanceHistory = async () => {
  return (await api.get("attendance/history/")).data;
};

// ------------------------------
// PROFILE
// ------------------------------
export const getProfileStatus = async () => {
  return (await api.get("user/profile-status/")).data;
};

export const updateProfile = async (payload) => {
  return (await api.post("user/update-profile/", payload)).data;
};

export const fetchProtected = (url, opts = {}) =>
  api.get(url, opts).then((res) => res.data);

export default api;

const API = import.meta.env.VITE_API_URL ;

export const checkHealth = async () =>
  fetch(`${API}/health`).then(r => r.json()).catch(() => null);

export const getUser = async (userId) =>
  fetch(`${API}/users/${userId}`).then(r => r.json());

export const getUserProgress = async (userId) =>
  fetch(`${API}/users/${userId}/progress`).then(r => r.json());

export const getProblems = async (difficulty = null) => {
  const url = difficulty ? `${API}/problems?difficulty=${difficulty}` : `${API}/problems`;
  return fetch(url).then(r => r.json());
};

export const getProblem = async (problemId) =>
  fetch(`${API}/problems/${problemId}`).then(r => r.json());

export const runCode = async (payload) =>
  fetch(`${API}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(r => r.json());

// === NEW FUNCTION ===
export const validateSolution = async (payload) =>
  fetch(`${API}/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(r => r.json());
// ====================

export const submitSolution = async (payload) =>
  fetch(`${API}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(r => r.json());

export const getFeedback = async (payload) =>
  fetch(`${API}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(r => r.json());

export const getLanguages = async () =>
  fetch(`${API}/languages`).then(r => r.json()).catch(() => []);

import { useEffect, useMemo, useRef, useState } from "react";
import LearningPage from "./pages/LearningPage";
import LabPage from "./pages/LabPage";
import QuizPage from "./pages/QuizPage";
import LoadingSpinner from "./components/LoadingSpinner";
import TeacherChat from "./components/TeacherChat";

const API_BASE = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;
const AUTH_STORAGE_KEY = "linux-course-auth";
const SELECTED_COURSE_STORAGE_KEY = "linux-course-selected-course";
const THEME_STORAGE_KEY = "linux-course-theme";
const HISTORY_VIEW_KEY = "linuxCourseView";
const HISTORY_COURSE_ID_KEY = "linuxCourseId";

function CheckIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <path
        d="M5 10.5 8.2 13.7 15 6.8"
        fill="none"
        stroke="currentColor"
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth="2"
      />
    </svg>
  );
}

function CircleIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <circle cx="10" cy="10" r="6.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg viewBox="0 0 20 20" aria-hidden="true">
      <rect x="5.2" y="8.6" width="9.6" height="7.2" rx="1.8" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="M7.2 8.6V6.8a2.8 2.8 0 0 1 5.6 0v1.8" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

function ThemeToggleButton({ theme, onToggleTheme }) {
  const dark = theme === "dark";

  return (
    <button
      className={`theme-toggle-button ${dark ? "is-dark" : ""}`}
      type="button"
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      aria-pressed={dark}
      onClick={onToggleTheme}
    >
      <span className="toggle__handler" aria-hidden="true">
        <span className="crater crater--1" />
        <span className="crater crater--2" />
        <span className="crater crater--3" />
      </span>
      <span className="star star--1" aria-hidden="true" />
      <span className="star star--2" aria-hidden="true" />
      <span className="star star--3" aria-hidden="true" />
      <span className="star star--4" aria-hidden="true" />
      <span className="star star--5" aria-hidden="true" />
      <span className="star star--6" aria-hidden="true" />
    </button>
  );
}

function UserMenu({ user, onCourses, onLogout, showCourses = false }) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;

    const handlePointerDown = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const runAction = (callback) => {
    setOpen(false);
    callback?.();
  };
  const initial = (user.username || user.email || "U").trim().charAt(0).toUpperCase();

  return (
    <div className="user-menu" ref={menuRef}>
      <button
        className={`topbar-user-card user-menu-trigger ${open ? "open" : ""}`}
        type="button"
        aria-label={`Open user menu for ${user.username}`}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="user-avatar" aria-hidden="true">{initial}</span>
      </button>

      {open && (
        <div className="user-menu-popover" role="menu" aria-label="User menu">
          <div className="user-menu-header">
            <span className="user-avatar large" aria-hidden="true">{initial}</span>
            <div>
              <span>Account</span>
              <strong>{user.username}</strong>
              <small>{user.email}</small>
            </div>
          </div>
          {showCourses && (
            <button className="user-menu-item" type="button" role="menuitem" onClick={() => runAction(onCourses)}>
              <span className="user-menu-item-icon" aria-hidden="true">
                <svg viewBox="0 0 20 20">
                  <path d="M4 5.5h12M4 10h12M4 14.5h8" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
                </svg>
              </span>
              Courses
            </button>
          )}
          <button className="user-menu-item danger" type="button" role="menuitem" onClick={() => runAction(onLogout)}>
            <span className="user-menu-item-icon" aria-hidden="true">
              <svg viewBox="0 0 20 20">
                <path d="M8.4 5H5.8A1.8 1.8 0 0 0 4 6.8v6.4A1.8 1.8 0 0 0 5.8 15h2.6M11.2 6.8 14.4 10l-3.2 3.2M7.8 10h6.4" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" />
              </svg>
            </span>
            Logout
          </button>
        </div>
      )}
    </div>
  );
}

function App() {
  const [auth, setAuth] = useState(() => {
    const saved = window.localStorage.getItem(AUTH_STORAGE_KEY);
    return saved ? JSON.parse(saved) : null;
  });
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({
    username: "",
    email: "",
    password: "",
    usernameOrEmail: "",
  });
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [theme, setTheme] = useState(() => window.localStorage.getItem(THEME_STORAGE_KEY) || "light");
  const [courses, setCourses] = useState([]);
  const [selectedCourseId, setSelectedCourseId] = useState(() => window.localStorage.getItem(SELECTED_COURSE_STORAGE_KEY));
  const [concepts, setConcepts] = useState([]);
  const [concept, setConcept] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [quizQuestionStart, setQuizQuestionStart] = useState(1);
  const [activeLab, setActiveLab] = useState(null);
  const [retryPrompt, setRetryPrompt] = useState(null);
  const [adaptiveMessage, setAdaptiveMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const quizDialogRef = useRef(null);

  useEffect(() => {
    if (!auth?.token) return;
    loadInitialData();
  }, [auth?.token]);

  useEffect(() => {
    document.documentElement.style.colorScheme = theme === "dark" ? "dark" : "light";
  }, [theme]);

  const quizQuestions = quiz?.questions || (quiz?.next_question ? [quiz.next_question] : []);
  const quizOpen = quizQuestions.length > 0 || Boolean(retryPrompt);
  const themeClass = theme === "dark" ? "theme-dark" : "theme-light";

  useEffect(() => {
    if (!quizOpen) return undefined;

    const previouslyFocused = document.activeElement;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = "";
      if (previouslyFocused instanceof HTMLElement) {
        previouslyFocused.focus();
      }
    };
  }, [quizOpen]);

  useEffect(() => {
    if (!quizOpen) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === "Escape" && !submitting) {
        returnToLesson();
        return;
      }

      if (event.key !== "Tab") return;

      const focusable = Array.from(
        quizDialogRef.current?.querySelectorAll(
          'button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href], [tabindex]:not([tabindex="-1"])'
        ) || []
      ).filter((element) => !element.hasAttribute("hidden"));

      if (focusable.length === 0) {
        event.preventDefault();
        quizDialogRef.current?.focus();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [quizOpen, submitting]);

  const selectedCourse = useMemo(
    () => courses.find((course) => String(course.id) === selectedCourseId) || null,
    [courses, selectedCourseId]
  );

  const visibleConcepts = useMemo(() => {
    if (!selectedCourse) return concepts;
    return concepts.filter((item) => item.course === selectedCourse.title);
  }, [concepts, selectedCourse]);

  const groupedConcepts = useMemo(() => {
    return visibleConcepts.reduce((groups, item) => {
      const moduleKey = item.module || "Course Module";
      const topicKey = item.topic || "Course Topic";

      if (!groups[moduleKey]) {
        groups[moduleKey] = {
          items: [],
          topics: {},
        };
      }
      if (!groups[moduleKey].topics[topicKey]) {
        groups[moduleKey].topics[topicKey] = [];
      }

      groups[moduleKey].items.push(item);
      groups[moduleKey].topics[topicKey].push(item);
      return groups;
    }, {});
  }, [visibleConcepts]);

  const currentConceptIndex = useMemo(
    () => visibleConcepts.findIndex((item) => item.lesson_id === concept?.lesson_id),
    [visibleConcepts, concept?.lesson_id]
  );
  const moduleNames = useMemo(() => Object.keys(groupedConcepts), [groupedConcepts]);
  const currentModuleNumber = Math.max(1, moduleNames.findIndex((moduleName) => moduleName === concept?.module) + 1);

  const previousLesson = currentConceptIndex > 0 ? visibleConcepts[currentConceptIndex - 1] : null;
  const nextLesson = currentConceptIndex >= 0 ? visibleConcepts[currentConceptIndex + 1] || null : null;

  const buildHeaders = (extraHeaders = {}) => ({
    ...extraHeaders,
    ...(auth?.token ? { Authorization: `Bearer ${auth.token}` } : {}),
  });

  const persistAuth = (nextAuth) => {
    setAuth(nextAuth);
    if (nextAuth) {
      window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(nextAuth));
    } else {
      window.localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  };

  const toggleTheme = () => {
    setTheme((current) => {
      const nextTheme = current === "dark" ? "light" : "dark";
      window.localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      return nextTheme;
    });
  };

  const currentHistoryState = () => {
    const state = window.history.state;
    return state && typeof state === "object" ? state : {};
  };

  const markHistoryAsHome = () => {
    window.history.replaceState(
      {
        ...currentHistoryState(),
        [HISTORY_VIEW_KEY]: "home",
        [HISTORY_COURSE_ID_KEY]: null,
      },
      "",
      window.location.href
    );
  };

  const ensureCourseHistory = (courseId) => {
    const normalizedCourseId = String(courseId);
    const state = currentHistoryState();

    if (state[HISTORY_VIEW_KEY] === "course") {
      window.history.replaceState(
        {
          ...state,
          [HISTORY_COURSE_ID_KEY]: normalizedCourseId,
        },
        "",
        window.location.href
      );
      return;
    }

    markHistoryAsHome();
    window.history.pushState(
      {
        ...currentHistoryState(),
        [HISTORY_VIEW_KEY]: "course",
        [HISTORY_COURSE_ID_KEY]: normalizedCourseId,
      },
      "",
      window.location.href
    );
  };

  const loadInitialData = async () => {
    setLoading(true);
    setError("");
    try {
      const loadedCourses = await fetchCourses();
      const loadedConcepts = await fetchConcepts();
      const restoredCourse = loadedCourses.find((course) => String(course.id) === selectedCourseId);

      if (selectedCourseId && !restoredCourse) {
        window.localStorage.removeItem(SELECTED_COURSE_STORAGE_KEY);
        setSelectedCourseId(null);
      }

      if (restoredCourse) {
        const resumeConcept = await fetchConcept();
        if (resumeConcept.course !== restoredCourse.title) {
          const courseConcepts = loadedConcepts.filter((item) => item.course === restoredCourse.title);
          const firstAvailable = courseConcepts.find((item) => !item.locked) || courseConcepts[0];
          if (firstAvailable) {
            await fetchConcept(firstAvailable.lesson_id);
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCourses = async () => {
    const response = await fetch(`${API_BASE}/courses`, {
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error("Unable to load courses.");
    }
    const data = await response.json();
    setCourses(data);
    return data;
  };

  const fetchConcepts = async () => {
    const response = await fetch(`${API_BASE}/concepts`, {
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error("Unable to load course concepts.");
    }
    const data = await response.json();
    setConcepts(data);
    return data;
  };

  const fetchConcept = async (lessonId = null) => {
    const params = new URLSearchParams();
    if (lessonId) {
      params.set("lesson_id", String(lessonId));
    }
    const query = params.toString();
    const response = await fetch(`${API_BASE}/lesson${query ? `?${query}` : ""}`, {
      headers: buildHeaders(),
    });
    if (!response.ok) {
      throw new Error("Unable to load the concept.");
    }
    const data = await response.json();
    setConcept(data);
    setActiveLab(null);
    setQuiz(null);
    setQuizQuestionStart(1);
    setRetryPrompt(null);
    return data;
  };

  const selectConcept = async (lessonId, locked = false) => {
    if (locked) return;
    setLoading(true);
    setError("");
    try {
      await fetchConcept(lessonId);
      await fetchConcepts();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuiz = async () => {
    if (!concept) return;
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({
        lesson_id: String(concept.lesson_id),
      });
      const response = await fetch(`${API_BASE}/quiz?${params.toString()}`, {
        headers: buildHeaders(),
      });
      if (!response.ok) {
        throw new Error("Unable to load quiz questions.");
      }
      const data = await response.json();
      setQuiz(data);
      setQuizQuestionStart(1);
      setRetryPrompt(data.retry_prompt || null);
      setAdaptiveMessage("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const runBash = async ({ exerciseId = null, labTaskId = null, sourceCode }) => {
    const response = await fetch(`${API_BASE}/runner/bash`, {
      method: "POST",
      headers: buildHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        exercise_id: exerciseId,
        lab_task_id: labTaskId,
        source_code: sourceCode,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to run Bash code.");
    }
    return data;
  };

  const askTeacher = async ({ message, history, onToken }) => {
    if (!concept) {
      throw new Error("Open a lesson before asking the teacher.");
    }

    const response = await fetch(`${API_BASE}/chat/teacher/stream`, {
      method: "POST",
      headers: buildHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({
        lesson_id: concept.lesson_id,
        level: concept.level || "standard",
        message,
        history,
        view: activeLab ? "lab" : "lesson",
        lab_id: activeLab?.id || null,
        lab_title: activeLab?.title || null,
      }),
    });
    if (!response.ok) {
      const text = await response.text();
      let detail = text;
      try {
        const data = JSON.parse(text);
        detail = data.detail || detail;
      } catch {
        // Keep the raw server text when the error is not JSON.
      }
      throw new Error(detail || "Unable to reach the teacher.");
    }

    if (!response.body) {
      const text = await response.text();
      onToken?.(text);
      return { reply: text };
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let reply = "";

    while (true) {
      const { value, done } = await reader.read();
      const chunk = decoder.decode(value || new Uint8Array(), { stream: !done });
      if (chunk) {
        reply += chunk;
        onToken?.(chunk);
      }
      if (done) break;
    }

    return { reply };
  };

  const submitQuiz = async (answers, decision = null) => {
    setSubmitting(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/submitQuiz`, {
        method: "POST",
        headers: buildHeaders({ "Content-Type": "application/json" }),
        body: JSON.stringify({
          lesson_id: concept.lesson_id,
          answers,
          decision,
        }),
      });
      if (!response.ok) {
        throw new Error("Unable to submit the quiz.");
      }
      const data = await response.json();

      if (data.next_question) {
        const nextQuestionStart = quizQuestionStart + quizQuestions.length;
        setRetryPrompt(null);
        setQuiz({
          lesson_id: concept.lesson_id,
          questions: [data.next_question],
        });
        setQuizQuestionStart(nextQuestionStart);
        setConcept((current) => ({
          ...current,
          attempts: (current?.attempts || 0) + 1,
        }));
      } else if (data.retry_prompt) {
        setRetryPrompt(data.retry_prompt);
      } else if (data.lesson_content_update) {
        setQuiz(null);
        setRetryPrompt(null);
        setAdaptiveMessage(data.lesson_content_update.adaptive_message || "");
        await fetchConcept(data.lesson_content_update.lesson_id);
        await fetchConcepts();
      } else if (data.lesson_complete) {
        setQuiz(null);
        setRetryPrompt(null);
        setAdaptiveMessage("");
        await fetchConcept(data.next_lesson_id || concept.lesson_id);
        await fetchConcepts();
      } else {
        setQuiz(null);
        setRetryPrompt(null);
        await fetchConcepts();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const returnToLesson = () => {
    if (submitting) return;
    setQuiz(null);
    setQuizQuestionStart(1);
    setRetryPrompt(null);
  };

  const launchLab = (lab) => {
    setActiveLab(lab);
    setQuiz(null);
    setQuizQuestionStart(1);
    setRetryPrompt(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openSidebarLab = async (lessonItem, labItem) => {
    if (!lessonItem || lessonItem.locked || !labItem) return;
    setLoading(true);
    setError("");
    try {
      const loadedConcept = concept?.lesson_id === lessonItem.lesson_id
        ? concept
        : await fetchConcept(lessonItem.lesson_id);
      const lab = loadedConcept?.labs?.find((item) => item.id === labItem.id) || labItem;
      launchLab(lab);
      await fetchConcepts();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const returnToLabLesson = () => {
    setActiveLab(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const keepPopupOpen = (event) => {
    event.stopPropagation();
  };

  const handleAuthFieldChange = (field, value) => {
    setAuthForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const submitAuth = async (event) => {
    event.preventDefault();
    setAuthLoading(true);
    setAuthError("");

    const endpoint = authMode === "register" ? "/auth/register" : "/auth/login";
    const payload = authMode === "register"
      ? {
          username: authForm.username.trim(),
          email: authForm.email.trim(),
          password: authForm.password,
        }
      : {
          username_or_email: authForm.usernameOrEmail.trim(),
          password: authForm.password,
        };

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Unable to sign in.");
      }

      persistAuth(data);
      setAuthForm({
        username: "",
        email: "",
        password: "",
        usernameOrEmail: "",
      });
    } catch (err) {
      setAuthError(err.message);
    } finally {
      setAuthLoading(false);
    }
  };

  const openCourse = async (course) => {
    ensureCourseHistory(course.id);
    window.localStorage.setItem(SELECTED_COURSE_STORAGE_KEY, String(course.id));
    setSelectedCourseId(String(course.id));
    setLoading(true);
    setError("");
    try {
      const latestConcepts = await fetchConcepts();
      const courseConcepts = latestConcepts.filter((item) => item.course === course.title);
      const firstAvailable = courseConcepts.find((item) => !item.locked) || courseConcepts[0];
      if (firstAvailable) {
        await fetchConcept(firstAvailable.lesson_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const clearCourseSelection = () => {
    window.localStorage.removeItem(SELECTED_COURSE_STORAGE_KEY);
    setSelectedCourseId(null);
    setConcept(null);
    setActiveLab(null);
    setQuiz(null);
    setRetryPrompt(null);
    setAdaptiveMessage("");
    setError("");
  };

  const returnHome = () => {
    if (currentHistoryState()[HISTORY_VIEW_KEY] === "course") {
      window.history.back();
      return;
    }

    clearCourseSelection();
  };

  const restoreCourseFromHistory = async (courseId) => {
    const normalizedCourseId = String(courseId);
    window.localStorage.setItem(SELECTED_COURSE_STORAGE_KEY, normalizedCourseId);
    setSelectedCourseId(normalizedCourseId);
    setLoading(true);
    setError("");

    try {
      const availableCourses = courses.length > 0 ? courses : await fetchCourses();
      const course = availableCourses.find((item) => String(item.id) === normalizedCourseId);

      if (!course) {
        markHistoryAsHome();
        clearCourseSelection();
        return;
      }

      const latestConcepts = await fetchConcepts();
      const courseConcepts = latestConcepts.filter((item) => item.course === course.title);
      const firstAvailable = courseConcepts.find((item) => !item.locked) || courseConcepts[0];
      if (firstAvailable) {
        await fetchConcept(firstAvailable.lesson_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    markHistoryAsHome();
    persistAuth(null);
    setCourses([]);
    window.localStorage.removeItem(SELECTED_COURSE_STORAGE_KEY);
    setSelectedCourseId(null);
    setConcepts([]);
    setConcept(null);
    setActiveLab(null);
    setQuiz(null);
    setRetryPrompt(null);
    setAdaptiveMessage("");
    setError("");
  };

  const navigateLesson = (targetLesson) => {
    if (!targetLesson || targetLesson.locked) return;
    selectConcept(targetLesson.lesson_id, targetLesson.locked);
  };

  useEffect(() => {
    if (!auth?.token || !selectedCourseId) return;
    ensureCourseHistory(selectedCourseId);
  }, [auth?.token, selectedCourseId]);

  useEffect(() => {
    if (!auth?.token) return undefined;

    const handlePopState = (event) => {
      const historyCourseId = event.state?.[HISTORY_COURSE_ID_KEY];
      if (event.state?.[HISTORY_VIEW_KEY] === "course" && historyCourseId) {
        restoreCourseFromHistory(historyCourseId);
        return;
      }

      clearCourseSelection();
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [auth?.token, courses]);

  if (!auth?.token) {
    return (
      <div className={`course-page auth-page ${themeClass}`}>
        <main className="auth-main">
          <section className="auth-panel">
            <div className="auth-panel-header">
              <div className="ui-eyebrow">Linux Course</div>
              <ThemeToggleButton theme={theme} onToggleTheme={toggleTheme} />
            </div>
            <h1 className="auth-title">{authMode === "register" ? "Create your account" : "Sign in to continue"}</h1>
            <p className="auth-copy">Your lesson progress stays tied to your account, so you can pick up where you left off.</p>

            <div className="auth-switch" role="group" aria-label="Authentication mode">
              <button
                className={`btn ${authMode === "login" ? "btn-primary" : ""}`}
                type="button"
                aria-pressed={authMode === "login"}
                onClick={() => {
                  setAuthMode("login");
                  setAuthError("");
                }}
              >
                Login
              </button>
              <button
                className={`btn ${authMode === "register" ? "btn-primary" : ""}`}
                type="button"
                aria-pressed={authMode === "register"}
                onClick={() => {
                  setAuthMode("register");
                  setAuthError("");
                }}
              >
                Register
              </button>
            </div>

            <form className="auth-form" onSubmit={submitAuth}>
              {authMode === "register" && (
                <label className="auth-field">
                  <span>Username</span>
                  <input
                    autoComplete="username"
                    value={authForm.username}
                    onChange={(event) => handleAuthFieldChange("username", event.target.value)}
                    required
                  />
                </label>
              )}
              {authMode === "register" && (
                <label className="auth-field">
                  <span>Email</span>
                  <input
                    autoComplete="email"
                    type="email"
                    value={authForm.email}
                    onChange={(event) => handleAuthFieldChange("email", event.target.value)}
                    required
                  />
                </label>
              )}
              {authMode === "login" && (
                <label className="auth-field">
                  <span>Username or email</span>
                  <input
                    autoComplete="username"
                    value={authForm.usernameOrEmail}
                    onChange={(event) => handleAuthFieldChange("usernameOrEmail", event.target.value)}
                    required
                  />
                </label>
              )}
              <label className="auth-field">
                <span>Password</span>
                <span className="password-field">
                  <input
                    type={showPassword ? "text" : "password"}
                    autoComplete={authMode === "register" ? "new-password" : "current-password"}
                    value={authForm.password}
                    onChange={(event) => handleAuthFieldChange("password", event.target.value)}
                    required
                  />
                  <button
                    className="password-toggle"
                    type="button"
                    onClick={() => setShowPassword((current) => !current)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? "Hide" : "Show"}
                  </button>
                </span>
              </label>

              {authError && <div className="error-box" role="alert">{authError}</div>}

              <button className="btn btn-primary auth-submit" type="submit" disabled={authLoading}>
                {authLoading ? "Please wait..." : authMode === "register" ? "Create account" : "Sign in"}
              </button>
            </form>
          </section>
        </main>
      </div>
    );
  }

  if (!selectedCourse) {
    return (
      <div className={`course-page home-page ${themeClass}`}>
        <main className="home-main">
          <header className="home-topbar">
            <div>
              <div className="ui-eyebrow">Learning platform</div>
              <h1 className="home-title">Choose a course</h1>
            </div>
            <div className="topbar-actions">
              <ThemeToggleButton theme={theme} onToggleTheme={toggleTheme} />
              <UserMenu user={auth.user} onLogout={logout} />
            </div>
          </header>

          {error && <div className="error-box" role="alert">{error}</div>}
          {loading && <LoadingSpinner message="Loading courses..." />}

          {!loading && !error && (
            <section className="course-grid" aria-label="Available courses">
              {courses.map((course) => {
                const courseConcepts = concepts.filter((item) => item.course === course.title);
                const masteredCount = courseConcepts.filter((item) => item.mastery_status === "mastered").length;
                const lessonCount = course.modules.reduce(
                  (moduleTotal, moduleItem) =>
                    moduleTotal + moduleItem.topics.reduce((topicTotal, topic) => topicTotal + topic.lessons.length, 0),
                  0
                );
                const topicCount = course.modules.reduce((total, moduleItem) => total + moduleItem.topics.length, 0);
                const progressTotal = courseConcepts.length || lessonCount;
                const progressPercent = progressTotal ? (masteredCount / progressTotal) * 100 : 0;

                return (
                  <article className="course-card" key={course.id}>
                    <div className="course-card-header">
                      <div>
                        <div className="course-card-kicker">Course {String(course.sequence).padStart(2, "0")}</div>
                        <h2>{course.title}</h2>
                      </div>
                      <span className="course-card-badge">{course.modules.length} modules</span>
                    </div>
                    <div className="course-stats">
                      <span>{topicCount} topics</span>
                      <span>{lessonCount} lessons</span>
                      <span>{masteredCount} completed</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill" style={{ width: `${progressPercent}%` }} />
                    </div>
                    <button className="btn btn-primary course-open" type="button" onClick={() => openCourse(course)}>
                      Open course
                    </button>
                  </article>
                );
              })}
              {courses.length === 0 && (
                <div className="empty-state" role="status">
                  <strong>No courses available</strong>
                  <span>Published courses will appear here when they are ready.</span>
                </div>
              )}
            </section>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className={`course-page ${themeClass}`}>
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-eyebrow">{concept?.course || "Linux Course"}</div>
          <div className="logo-title">
            {concept?.module || "Course"} <span className="logo-badge">{String(currentModuleNumber).padStart(2, "0")}</span>
          </div>
        </div>

        {Object.entries(groupedConcepts).map(([moduleName, moduleGroup]) => (
          <div key={moduleName}>
            <div className="sidebar-section-label">{moduleName}</div>
            <div className="sidebar-progress">
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${moduleGroup.items.length ? (moduleGroup.items.filter((item) => item.mastery_status === "mastered").length / moduleGroup.items.length) * 100 : 0}%` }}
                />
              </div>
              <div className="progress-label">
                {moduleGroup.items.filter((item) => item.mastery_status === "mastered").length} of {moduleGroup.items.length} lessons done
              </div>
            </div>
            {Object.entries(moduleGroup.topics).map(([topicName, sublevels], topicIndex) => (
              <div className="sidebar-topic" key={topicName}>
                <div className="sidebar-topic-label">
                  <span>topic {String(topicIndex + 1).padStart(2, "0")}</span>
                  <strong>{topicName}</strong>
                </div>
                {sublevels.map((item) => (
                  <button
                    key={item.lesson_id}
                    className={`sidebar-item sidebar-sublevel ${item.locked ? "locked" : ""} ${!activeLab && concept?.lesson_id === item.lesson_id ? "active" : ""}`}
                    type="button"
                    onClick={() => selectConcept(item.lesson_id, item.locked)}
                    disabled={item.locked}
                  >
                    <span className="sidebar-item-copy">
                      <span className="sidebar-item-title">{item.title}</span>
                    </span>
                    <span
                      className={`sidebar-item-status ${item.locked ? "locked" : item.mastery_status === "mastered" ? "done" : !activeLab && concept?.lesson_id === item.lesson_id ? "active" : "upcoming"}`}
                      title={item.locked ? "Complete previous sublevels to unlock." : undefined}
                    >
                      {item.locked ? (
                        <LockIcon />
                      ) : item.mastery_status === "mastered" ? (
                        <CheckIcon />
                      ) : (
                        <CircleIcon />
                      )}
                    </span>
                  </button>
                ))}
                {sublevels.flatMap((item) =>
                  (item.labs || []).map((lab) => (
                    <button
                      key={`lab-${lab.id}`}
                      className={`sidebar-item sidebar-sublevel sidebar-lab ${item.locked ? "locked" : ""} ${activeLab?.id === lab.id ? "active" : ""}`}
                      type="button"
                      onClick={() => openSidebarLab(item, lab)}
                      disabled={item.locked}
                    >
                      <span className="sidebar-item-copy">
                        <span className="sidebar-item-kicker">Lab</span>
                        <span className="sidebar-item-title">{lab.title || "Topic Lab"}</span>
                      </span>
                      <span
                        className={`sidebar-item-status ${item.locked ? "locked" : activeLab?.id === lab.id ? "active" : "upcoming"}`}
                        title={item.locked ? "Complete previous sublevels to unlock this lab." : undefined}
                      >
                        {item.locked ? <LockIcon /> : <CircleIcon />}
                      </span>
                    </button>
                  ))
                )}
              </div>
            ))}
          </div>
        ))}

      </aside>

      <main className="main">
        <div className="topbar">
          <div className="topbar-copy">
            <div className="ui-eyebrow">{concept?.course || "Linux course"}</div>
            <div className="topbar-title-row">
              <h1 className="topbar-title">{activeLab?.title || concept?.title || "Select a lesson"}</h1>
              {concept?.level && <span className="topbar-pill">{concept.level.toUpperCase()}</span>}
            </div>
            <div className="breadcrumb">
              <span>{concept?.course || "course"}</span>
              <span className="bc-sep">/</span>
              <span>{concept?.module || "module"}</span>
              <span className="bc-sep">/</span>
              <span>{concept?.topic || "topic"}</span>
              <span className="bc-sep">/</span>
              <span className="current">{activeLab?.title || concept?.title || "lesson"}</span>
            </div>
          </div>
          <div className="topbar-actions">
            <ThemeToggleButton theme={theme} onToggleTheme={toggleTheme} />
            <UserMenu
              user={auth.user}
              onCourses={returnHome}
              onLogout={logout}
              showCourses
            />
          </div>
        </div>

        <div className="content">
          {error && <div className="error-box" role="alert">{error}</div>}
          {loading && <LoadingSpinner message="Loading lesson..." />}

          {!loading && concept && (
            <>
              {activeLab ? (
                <LabPage
                  concept={concept}
                  lab={activeLab}
                  onRunBash={runBash}
                  onBackToLesson={returnToLabLesson}
                  onHome={returnHome}
                />
              ) : (
                <LearningPage
                  concept={concept}
                  onStartQuiz={fetchQuiz}
                  onRunBash={runBash}
                  adaptiveMessage={adaptiveMessage}
                  previousLesson={previousLesson}
                  nextLesson={nextLesson}
                  onPreviousLesson={() => navigateLesson(previousLesson)}
                  onNextLesson={() => navigateLesson(nextLesson)}
                  onHome={returnHome}
                />
              )}

              {!activeLab && quizOpen && (
                <div className="quiz-modal-backdrop" onClick={returnToLesson} role="presentation">
                  <div
                    className="quiz-modal"
                    ref={quizDialogRef}
                    tabIndex="-1"
                    onClick={keepPopupOpen}
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="quiz-title"
                  >
                    <QuizPage
                      concept={concept}
                      questions={quizQuestions}
                      onSubmit={submitQuiz}
                      onCancel={returnToLesson}
                      questionNumberStart={quizQuestionStart}
                      submitting={submitting}
                      error={error}
                      retryPrompt={retryPrompt}
                      onRetryQuestions={() => submitQuiz([], "retry_questions")}
                      onReviewLesson={() => submitQuiz([], "review_lesson")}
                    />
                  </div>
                </div>
              )}
              <TeacherChat concept={concept} activeLab={activeLab} onAskTeacher={askTeacher} />
            </>
          )}
          {!loading && !error && !concept && (
            <div className="empty-state" role="status">
              <strong>No lesson selected</strong>
              <span>Choose an available lesson from the course navigation to begin.</span>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;

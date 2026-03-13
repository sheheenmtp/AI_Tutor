import { useEffect, useState, useRef } from "react";
import Header from "./components/Header";
import ProblemSidebar from "./components/ProblemSidebar";
import CodeEditor from "./components/CodeEditor";
import ResultsPanel from "./components/ResultsPanel";
import {
  checkHealth,
  getUserProgress,
  getProblem,
  validateSolution,
  submitSolution,
  getFeedbackStream,
  registerUser,
  loginUser,
} from "./services/api";

export default function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });
  const [health, setHealth] = useState(null);
  const [user, setUser] = useState(null);
  const [progress, setProgress] = useState(null);
  const [currentProblem, setCurrentProblem] = useState(null);
  const [sampleTests, setSampleTests] = useState([]);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);

  const [runOutput, setRunOutput] = useState("");
  const [submissionResult, setSubmissionResult] = useState(null);
  const [aiFeedback, setAiFeedback] = useState("");
  const [authUser, setAuthUser] = useState(() => {
    const raw = localStorage.getItem("auth-user");
    return raw ? JSON.parse(raw) : null;
  });
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({ username: "", password: "" });
  const [authError, setAuthError] = useState("");
  const [authLoading, setAuthLoading] = useState(false);

  const userId = authUser?.id ?? null;

  // Refs for resize elements
  const sidebarRef = useRef(null);
  const resultsContainerRef = useRef(null);
  const editorContainerRef = useRef(null);
  const rightPanelRef = useRef(null);
  const verticalHandleRef = useRef(null);
  const horizontalHandleRef = useRef(null);
  const workspaceRef = useRef(null);

  // Run button removed - only Validate and Submit remain
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    checkHealth().then(setHealth);
    const interval = setInterval(() => checkHealth().then(setHealth), 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!userId) {
      setUser(null);
      setProgress(null);
      setCurrentProblem(null);
      return;
    }
    loadProgress(userId);
  }, [userId]);

  const handleVerticalResizeStart = (event) => {
    event.preventDefault();
    const handle = verticalHandleRef.current;
    const sidebar = sidebarRef.current;
    if (!handle || !sidebar) return;

    const startX = event.clientX;
    const startWidth = sidebar.getBoundingClientRect().width;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";
    handle.classList.add("dragging");

    const onMouseMove = (moveEvent) => {
      const newWidth = startWidth + (moveEvent.clientX - startX);
      const minWidth = 260;
      const maxWidth = window.innerWidth * 0.6;
      const constrainedWidth = Math.min(Math.max(newWidth, minWidth), maxWidth);
      sidebar.style.width = `${constrainedWidth}px`;
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      handle.classList.remove("dragging");
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  const handleHorizontalResizeStart = (event) => {
    event.preventDefault();
    const handle = horizontalHandleRef.current;
    const resultsContainer = resultsContainerRef.current;
    const editorContainer = editorContainerRef.current;
    const rightPanel = rightPanelRef.current;
    if (!handle || !resultsContainer || !editorContainer || !rightPanel) return;

    const startY = event.clientY;
    const startResultsHeight = resultsContainer.getBoundingClientRect().height;
    const totalContainerHeight = rightPanel.getBoundingClientRect().height;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "row-resize";
    handle.classList.add("dragging");
    editorContainer.classList.add("resizing");

    const onMouseMove = (moveEvent) => {
      const deltaY = moveEvent.clientY - startY;
      const newResultsHeight = startResultsHeight - deltaY;
      const minHeight = 120;
      const maxHeight = totalContainerHeight * 0.75;
      const constrainedResultsHeight = Math.min(Math.max(newResultsHeight, minHeight), maxHeight);

      resultsContainer.style.flex = "0 0 auto";
      resultsContainer.style.height = `${constrainedResultsHeight}px`;
    };

    const onMouseUp = () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      handle.classList.remove("dragging");
      editorContainer.classList.remove("resizing");
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  // Handle window resize for responsive adjustments
  useEffect(() => {
    const handleWindowResize = () => {
      // Reset any fixed heights to allow responsive behavior
      if (resultsContainerRef.current) {
        resultsContainerRef.current.style.height = "";
        resultsContainerRef.current.style.flex = "";
      }
      if (sidebarRef.current) {
        sidebarRef.current.style.width = "";
      }
      // Reset editor container styles
      if (editorContainerRef.current) {
        editorContainerRef.current.style.height = "";
        editorContainerRef.current.style.flex = "";
      }
    };

    window.addEventListener('resize', handleWindowResize);
    return () => window.removeEventListener('resize', handleWindowResize);
  }, []);

  const loadProgress = async (uid = userId) => {
    const prog = await getUserProgress(uid);
    setUser(prog.user);
    setProgress(prog);

    if (prog.next_problem) {
      loadProblem(prog.next_problem.id);
    }
  };

  const loadProblem = async (problemId) => {
    const data = await getProblem(problemId);
    setCurrentProblem(data.problem);
    setSampleTests(data.sample_test_cases);

    const savedCode = localStorage.getItem(`code-save-${problemId}`);
    if (savedCode) {
      setCode(savedCode);
    } else {
      setCode(data.problem.starter_code);
    }

    setRunOutput("");
    setSubmissionResult(null);
    setAiFeedback("");
  };

  const handleValidate = async () => {
    if (!currentProblem || !userId) return;

    setLoading(true);
    setRunOutput("");
    setSubmissionResult(null);
    setAiFeedback("");

    try {
      const res = await validateSolution({
        user_id: userId,
        problem_id: currentProblem.id,
        code,
        language_id: 71,
      });

      setSubmissionResult(res);
      setRunOutput(
        `Passed ${res.passed_tests}/${res.total_tests} tests · Score ${res.score}/${res.max_score}`
      );
    } catch (e) {
      setRunOutput(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!currentProblem || !userId) return;

    setLoading(true);
    setRunOutput("");
    setSubmissionResult(null);
    setAiFeedback("");

    try {
      const res = await submitSolution({
        user_id: userId,
        problem_id: currentProblem.id,
        code,
        language_id: 71,
      });

      setSubmissionResult(res);
      setRunOutput(
        `Passed ${res.passed_tests}/${res.total_tests} tests · Score ${res.score}/${res.max_score}`
      );

      if (res.all_passed) {
        localStorage.removeItem(`code-save-${currentProblem.id}`);
        setTimeout(() => loadProgress(), 1000);
      }
    } catch (e) {
      setRunOutput(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleGetHint = async () => {
    if (!runOutput || !user || !currentProblem) return;

    setLoading(true);
    setAiFeedback("");

    try {
      const expectedOutput =
        sampleTests.length > 0
          ? sampleTests[0].expected_output
          : "";

      await getFeedbackStream({
        level: user.current_level,
        problem_description: currentProblem.description,
        user_code: code,
        expected_output: expectedOutput,
        actual_output: runOutput,
      }, (chunk) => {
        setAiFeedback((prev) => prev + chunk);
      });
    } catch (e) {
      setAiFeedback(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleNextProblem = () => {
    if (progress?.next_problem) {
      loadProblem(progress.next_problem.id);
    }
  };

  const handleAuthChange = (field, value) => {
    setAuthForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError("");
    try {
      const payload = {
        username: authForm.username.trim(),
        password: authForm.password,
      };
      const result = authMode === "register"
        ? await registerUser(payload)
        : await loginUser(payload);
      setAuthUser(result.user);
      localStorage.setItem("auth-user", JSON.stringify(result.user));
      setAuthForm({ username: "", password: "" });
    } catch (err) {
      setAuthError(err.message || "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("auth-user");
    setAuthUser(null);
    setUser(null);
    setProgress(null);
    setCurrentProblem(null);
    setCode("");
    setRunOutput("");
    setSubmissionResult(null);
    setAiFeedback("");
  };

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  if (!authUser) {
    return (
      <div className="app loading-screen" style={{ justifyContent: "center", alignItems: "center" }}>
        <form
          onSubmit={handleAuthSubmit}
          style={{
            width: "100%",
            maxWidth: 360,
            background: "var(--bg-secondary)",
            border: "1px solid var(--border-primary)",
            borderRadius: 12,
            padding: 20,
            display: "flex",
            flexDirection: "column",
            gap: 12
          }}
        >
          <h2 style={{ margin: 0 }}>{authMode === "login" ? "Login" : "Register"}</h2>
          <input
            value={authForm.username}
            onChange={(e) => handleAuthChange("username", e.target.value)}
            placeholder="Username"
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid var(--border-primary)" }}
          />
          <input
            type="password"
            value={authForm.password}
            onChange={(e) => handleAuthChange("password", e.target.value)}
            placeholder="Password"
            required
            style={{ padding: 10, borderRadius: 8, border: "1px solid var(--border-primary)" }}
          />
          {authError && <div style={{ color: "#ef4444", fontSize: 13 }}>{authError}</div>}
          <button
            type="submit"
            disabled={authLoading}
            style={{
              padding: "10px 12px",
              borderRadius: 8,
              border: "none",
              background: "var(--color-purple)",
              color: "white",
              cursor: "pointer"
            }}
          >
            {authLoading ? "Please wait..." : authMode === "login" ? "Login" : "Create account"}
          </button>
          <button
            type="button"
            onClick={() => {
              setAuthMode((m) => (m === "login" ? "register" : "login"));
              setAuthError("");
            }}
            style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
          >
            {authMode === "login" ? "Need an account? Register" : "Already have an account? Login"}
          </button>
        </form>
      </div>
    );
  }

  if (!currentProblem) {
    return (
      <div className="app loading-screen">
        <div className="loader">
          <div className="loader-spinner"></div>
          <p>Loading Code Mastery...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header
        user={user}
        theme={theme}
        onThemeToggle={toggleTheme}
        onLogout={handleLogout}
      />

      <div className="workspace" ref={workspaceRef}>
        <div className="sidebar-pane" ref={sidebarRef}>
          <ProblemSidebar
            problem={currentProblem}
            sampleTests={sampleTests}
            solvedProblems={progress?.solved_problems || []}
            onNextProblem={handleNextProblem}
          />
        </div>
        <div
          className="vertical-resize-handle"
          ref={verticalHandleRef}
          onMouseDown={handleVerticalResizeStart}
        ></div>
        <div className="right-panel" ref={rightPanelRef}>
          <div className="editor-pane" ref={editorContainerRef}>
            <CodeEditor
              code={code}
              setCode={setCode}
              onValidate={handleValidate}
              onSubmit={handleSubmit}
              onGetHint={handleGetHint}
              loading={loading}
              hasOutput={!!runOutput || !!submissionResult}
              theme={theme}
              currentProblemId={currentProblem?.id}
            />
          </div>
          <div
            className="horizontal-resize-handle"
            ref={horizontalHandleRef}
            onMouseDown={handleHorizontalResizeStart}
          ></div>
          <div className="results-pane" ref={resultsContainerRef}>
            <ResultsPanel
              runOutput={runOutput}
              submissionResult={submissionResult}
              aiFeedback={aiFeedback}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

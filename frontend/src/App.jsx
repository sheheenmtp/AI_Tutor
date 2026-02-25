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
  getFeedback,
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

  const userId = 3;

  // Refs for resize elements
  const sidebarRef = useRef(null);
  const resultsContainerRef = useRef(null);
  const workspaceRef = useRef(null);

  // Run button removed - only Validate and Submit remain
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    loadProgress();
    checkHealth().then(setHealth);

    const interval = setInterval(() => {
      checkHealth().then(setHealth);
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  // Initialize vertical resize functionality
  useEffect(() => {
    const initVerticalResize = () => {
      const handle = document.querySelector('.vertical-resize-handle');
      const sidebar = sidebarRef.current;

      if (!handle || !sidebar) {
        // Retry after a short delay if elements aren't ready
        setTimeout(initVerticalResize, 100);
        return;
      }

      const onMouseDown = (e) => {
        e.preventDefault();
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';
        handle.classList.add('dragging');

        const startX = e.clientX;
        const startWidth = parseInt(document.defaultView.getComputedStyle(sidebar).width, 10);

        const doDrag = (e) => {
          const newWidth = startWidth + (e.clientX - startX);
          // Apply constraints: min 200px, max 50% of viewport
          const minWidth = 200;
          const maxWidth = window.innerWidth * 0.5;
          const constrainedWidth = Math.min(Math.max(newWidth, minWidth), maxWidth);
          sidebar.style.width = `${constrainedWidth}px`;
        };

        const stopDrag = () => {
          document.removeEventListener('mousemove', doDrag);
          document.removeEventListener('mouseup', stopDrag);
          document.body.style.userSelect = '';
          document.body.style.cursor = '';
          handle.classList.remove('dragging');
        };

        document.addEventListener('mousemove', doDrag);
        document.addEventListener('mouseup', stopDrag);
      };

      handle.addEventListener('mousedown', onMouseDown);

      // Cleanup function
      return () => {
        handle.removeEventListener('mousedown', onMouseDown);
      };
    };

    initVerticalResize();
  }, []);

  // Initialize horizontal resize functionality
  useEffect(() => {
    const initHorizontalResize = () => {
      const handle = document.querySelector('.horizontal-resize-handle');
      const resultsContainer = resultsContainerRef.current;
      const editorContainer = document.querySelector('.editor-container');

      if (!handle || !resultsContainer || !editorContainer) {
        // Retry after a short delay if elements aren't ready
        setTimeout(initHorizontalResize, 100);
        return;
      }

      const onMouseDown = (e) => {
        e.preventDefault();
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'row-resize';
        handle.classList.add('dragging');
        editorContainer.classList.add('resizing');
        const editorWrapper = editorContainer.querySelector('.editor-wrapper');
        if (editorWrapper) {
          editorWrapper.classList.add('resizing');
        }

        const startY = e.clientY;
        const startResultsHeight = parseInt(document.defaultView.getComputedStyle(resultsContainer).height, 10);
        const totalContainerHeight = resultsContainer.parentElement.clientHeight;

        const doDrag = (e) => {
          const deltaY = e.clientY - startY;
          const newResultsHeight = startResultsHeight - deltaY;

          // Apply constraints: min 80px, max 70% of right panel height
          const minHeight = 80;
          const maxHeight = totalContainerHeight * 0.7;
          const constrainedResultsHeight = Math.min(Math.max(newResultsHeight, minHeight), maxHeight);

          // Update flex properties instead of fixed heights for better responsiveness
          resultsContainer.style.flex = 'none';
          resultsContainer.style.height = `${constrainedResultsHeight}px`;

          // Adjust editor container to fill remaining space
          editorContainer.style.flex = 'none';
          const editorHeight = totalContainerHeight - constrainedResultsHeight - 4; // 4px for handle
          editorContainer.style.height = `${editorHeight}px`;
        };

        const stopDrag = () => {
          document.removeEventListener('mousemove', doDrag);
          document.removeEventListener('mouseup', stopDrag);
          document.body.style.userSelect = '';
          document.body.style.cursor = '';
          handle.classList.remove('dragging');
          editorContainer.classList.remove('resizing');
          const editorWrapper = editorContainer.querySelector('.editor-wrapper');
          if (editorWrapper) {
            editorWrapper.classList.remove('resizing');
          }
        };

        document.addEventListener('mousemove', doDrag);
        document.addEventListener('mouseup', stopDrag);
      };

      handle.addEventListener('mousedown', onMouseDown);

      // Cleanup function
      return () => {
        handle.removeEventListener('mousedown', onMouseDown);
      };
    };

    initHorizontalResize();
  }, []);

  // Handle window resize for responsive adjustments
  useEffect(() => {
    const handleWindowResize = () => {
      // Reset any fixed heights to allow responsive behavior
      if (resultsContainerRef.current) {
        resultsContainerRef.current.style.height = '';
        resultsContainerRef.current.style.flex = ''; // Reset flex property
      }
      if (sidebarRef.current) {
        sidebarRef.current.style.width = '';
      }
      // Reset editor container styles
      const editorContainer = document.querySelector('.editor-container');
      if (editorContainer) {
        editorContainer.style.height = '';
        editorContainer.style.flex = ''; // Reset flex property
      }
    };

    window.addEventListener('resize', handleWindowResize);
    return () => window.removeEventListener('resize', handleWindowResize);
  }, []);

  const loadProgress = async () => {
    const prog = await getUserProgress(userId);
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
    if (!currentProblem) return;

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
    if (!currentProblem) return;

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
        setTimeout(loadProgress, 1000);
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

    try {
      const expectedOutput =
        sampleTests.length > 0
          ? sampleTests[0].expected_output
          : "";

      const fb = await getFeedback({
        level: user.current_level,
        problem_description: currentProblem.description,
        user_code: code,
        expected_output: expectedOutput,
        actual_output: runOutput,
      });

      setAiFeedback(fb.feedback);
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

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

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
        progress={progress}
        health={health}
        theme={theme}
        onThemeToggle={toggleTheme}
      />

      <div className="workspace" ref={workspaceRef}>
        <div className="sidebar" ref={sidebarRef}>
          <ProblemSidebar
            problem={currentProblem}
            sampleTests={sampleTests}
            solvedProblems={progress?.solved_problems || []}
            onNextProblem={handleNextProblem}
          />
        </div>
        <div className="vertical-resize-handle"></div>
        <div className="right-panel">
          <div className="editor-container">
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
          <div className="horizontal-resize-handle"></div>
          <div className="results-container" ref={resultsContainerRef}>
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
import { useEffect, useState } from "react";

export default function LabPage({ concept, lab, onRunBash, onBackToLesson, onHome }) {
  const [codeByTask, setCodeByTask] = useState({});
  const [resultByTask, setResultByTask] = useState({});
  const [errorByTask, setErrorByTask] = useState({});
  const [runningTaskId, setRunningTaskId] = useState(null);

  useEffect(() => {
    const nextCodes = {};
    lab.tasks.forEach((task) => {
      nextCodes[task.id] = task.starter_code || "";
    });
    setCodeByTask(nextCodes);
    setResultByTask({});
    setErrorByTask({});
    setRunningTaskId(null);
  }, [lab.id, lab.tasks]);

  const runTask = async (task) => {
    if (!onRunBash || runningTaskId) return;
    setRunningTaskId(task.id);
    setErrorByTask((current) => ({ ...current, [task.id]: "" }));
    setResultByTask((current) => ({ ...current, [task.id]: null }));

    try {
      const result = await onRunBash({
        labTaskId: task.id,
        sourceCode: codeByTask[task.id] || "",
      });
      setResultByTask((current) => ({ ...current, [task.id]: result }));
    } catch (err) {
      setErrorByTask((current) => ({
        ...current,
        [task.id]: err.message || "Unable to run Bash code.",
      }));
    } finally {
      setRunningTaskId(null);
    }
  };

  return (
    <>
      <section className="lab-page-topbar">
        <div>
          <div className="ui-eyebrow">{concept.course}</div>
          <h2>{lab.title}</h2>
          <p>{lab.description}</p>
        </div>
        <div className="lab-page-actions">
          <button className="btn" type="button" onClick={onHome}>
            Home
          </button>
          <button className="btn" type="button" onClick={onBackToLesson}>
            Back to lesson
          </button>
        </div>
      </section>

      <section className="lab-workspace">
        <aside className="lab-brief">
          <div className="section-label bash-label">Guided Lab</div>
          <h3>{concept.title}</h3>
          <p>
            Complete the tasks in order. Each task runs in its own sandbox, so write commands that fully solve that
            task by themselves.
          </p>
          <div className="lab-summary">
            <span>{lab.tasks.length} tasks</span>
            <span>{lab.is_required ? "Required" : "Optional"}</span>
          </div>
        </aside>

        <div className="lab-task-list lab-page-task-list">
          {lab.tasks.length === 0 && (
            <div className="empty-state" role="status">
              <strong>No lab tasks available</strong>
              <span>This lab does not have any runnable tasks yet.</span>
            </div>
          )}
          {lab.tasks.map((task, index) => {
            const result = resultByTask[task.id];
            const error = errorByTask[task.id];
            const output = result?.stdout || result?.stderr || result?.compile_output || result?.message || "";

            return (
              <article
                className={`lab-task-card lab-page-task-card ${result?.passed ? "completed" : ""}`}
                key={task.id}
                aria-busy={runningTaskId === task.id}
              >
                <div className="lab-task-header">
                  <div>
                    <span className="lab-task-index">Task {index + 1}</span>
                    <h4>{task.title}</h4>
                  </div>
                  {result?.status?.description && (
                    <span className={`bash-status ${result.passed ? "passed" : ""}`}>
                      {result.passed ? "Passed" : result.status.description}
                    </span>
                  )}
                </div>
                <p>{task.instruction}</p>
                <textarea
                  className="bash-editor lab-editor"
                  value={codeByTask[task.id] || ""}
                  onChange={(event) => setCodeByTask((current) => ({ ...current, [task.id]: event.target.value }))}
                  aria-label={`Bash code for task ${index + 1}: ${task.title}`}
                  spellCheck="false"
                />
                <div className="bash-exercise-meta">
                  <span>Allowed: {task.allowed_commands.join(", ")}</span>
                  {task.expected_output && <span>Expected: {task.expected_output}</span>}
                </div>
                <div className="bash-actions">
                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={() => runTask(task)}
                    disabled={Boolean(runningTaskId)}
                  >
                    {runningTaskId === task.id ? "Running..." : "Run task"}
                  </button>
                  {result?.time && <span>{result.time}s</span>}
                </div>
                {(output || error) && (
                  <pre
                    className={`bash-output ${error ? "error" : ""}`}
                    role={error ? "alert" : "status"}
                    aria-live="polite"
                  >
                    {error || output}
                  </pre>
                )}
              </article>
            );
          })}
        </div>
      </section>
    </>
  );
}

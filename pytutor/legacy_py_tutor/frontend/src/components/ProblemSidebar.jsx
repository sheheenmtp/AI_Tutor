import { BookOpen, Lightbulb, ArrowRight, CheckCircle2, TestTube } from 'lucide-react';

export default function ProblemSidebar({ 
  problem, 
  sampleTests, 
  solvedProblems,
  onNextProblem 
}) {
  const getDifficultyClass = (diff) => {
    if (diff === "beginner") return "difficulty-easy";
    if (diff === "intermediate") return "difficulty-medium";
    return "difficulty-hard";
  };

  const isSolved = solvedProblems.includes(problem.id);

  return (
    <aside className="sidebar">
      <div className="sidebar-content">
        <div className="problem-header">
          <div className="problem-title-row">
            <h1 className="problem-title">{problem.title}</h1>
            {isSolved && (
              <span className="solved-badge">
                <CheckCircle2 size={14} />
                Solved
              </span>
            )}
          </div>
          <span className={`difficulty-badge ${getDifficultyClass(problem.difficulty)}`}>
            {problem.difficulty}
          </span>
        </div>

        <div className="problem-section">
          <div className="section-header">
            <BookOpen size={18} />
            <h3>Description</h3>
          </div>
          <div className="problem-description">
            {problem.description.split('\n').map((line, i) => (
              <p key={i}>{line}</p>
            ))}
          </div>
        </div>

        {sampleTests && sampleTests.length > 0 && (
          <div className="problem-section">
            <div className="section-header">
              <TestTube size={18} />
              <h3>Examples</h3>
            </div>
            <div className="examples-container">
              {sampleTests.map((test, i) => (
                <div key={i} className="example-card">
                  <div className="example-header">Example {i + 1}</div>
                  <div className="example-content">
                    {test.input_data && (
                      <div className="example-item">
                        <div className="example-label">Input:</div>
                        <pre className="example-code">{test.input_data}</pre>
                      </div>
                    )}
                    <div className="example-item">
                      <div className="example-label">Output:</div>
                      <pre className="example-code">{test.expected_output}</pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {problem.hints && problem.hints.length > 0 && (
          <div className="problem-section">
            <div className="section-header">
              <Lightbulb size={18} />
              <h3>Hints</h3>
            </div>
            <div className="hints-container">
              {problem.hints.map((hint, i) => (
                <div key={i} className="hint-card">
                  <div className="hint-number">{i + 1}</div>
                  <div className="hint-text">{hint}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {isSolved && (
        <div className="sidebar-footer">
          <button className="next-problem-btn" onClick={onNextProblem}>
            Next Problem
            <ArrowRight size={18} />
          </button>
        </div>
      )}
    </aside>
  );
}
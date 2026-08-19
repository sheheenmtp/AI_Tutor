import { useMemo, useState } from "react";
import { CheckCircle2, Compass, Search } from "lucide-react";

const normalizeDifficulty = (value = "") =>
  value.toLowerCase().trim().replace(/\s+/g, "_");

const canonicalDifficulty = (value = "") => {
  const normalized = normalizeDifficulty(value);
  if (normalized === "advanced_1" || normalized === "advanced1") return "expert";
  return normalized;
};

const difficultyLabel = (value = "") => {
  const normalized = canonicalDifficulty(value);
  if (!normalized) return "Unknown";
  return normalized
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
};

const difficultyClass = (value = "") => {
  const normalized = canonicalDifficulty(value);
  if (normalized === "beginner") return "difficulty-easy";
  if (normalized === "intermediate") return "difficulty-medium";
  return "difficulty-hard";
};

export default function QuestionBank({
  problems,
  solvedProblems,
  recommendedProblemId,
  onSelectProblem,
}) {
  const [query, setQuery] = useState("");
  const [showSolved, setShowSolved] = useState(true);
  const [showUnsolved, setShowUnsolved] = useState(true);
  const [difficultyFilters, setDifficultyFilters] = useState([]);

  const solvedSet = useMemo(() => new Set(solvedProblems || []), [solvedProblems]);

  const difficultyOptions = useMemo(() => {
    const values = new Set();
    for (const problem of problems || []) {
      values.add(canonicalDifficulty(problem?.difficulty || ""));
    }
    return Array.from(values).filter(Boolean).sort();
  }, [problems]);

  const filteredProblems = useMemo(() => {
    const text = query.trim().toLowerCase();
    return (problems || []).filter((problem) => {
      const isSolved = solvedSet.has(problem.id);
      if (!showSolved && isSolved) return false;
      if (!showUnsolved && !isSolved) return false;

      if (difficultyFilters.length > 0) {
        const currentDifficulty = canonicalDifficulty(problem.difficulty || "");
        if (!difficultyFilters.includes(currentDifficulty)) return false;
      }

      if (!text) return true;

      const title = (problem.title || "").toLowerCase();
      const concept = (problem.concept_id || "").toLowerCase();
      const description = (problem.description || "").toLowerCase();
      return (
        title.includes(text) ||
        concept.includes(text) ||
        description.includes(text) ||
        String(problem.order_index || "").includes(text)
      );
    });
  }, [problems, solvedSet, showSolved, showUnsolved, difficultyFilters, query]);

  const toggleDifficulty = (difficulty) => {
    setDifficultyFilters((prev) =>
      prev.includes(difficulty)
        ? prev.filter((item) => item !== difficulty)
        : [...prev, difficulty]
    );
  };

  return (
    <div className="question-bank-page">
      <div className="question-bank-main">
        <div className="question-bank-toolbar">
          <div className="question-bank-search">
            <Search size={16} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by title, concept, or index..."
            />
          </div>
          <div className="question-bank-count">
            {filteredProblems.length} / {problems.length} questions
          </div>
        </div>

        <div className="question-list">
          {filteredProblems.map((problem) => {
            const isSolved = solvedSet.has(problem.id);
            const isRecommended = recommendedProblemId === problem.id;
            return (
              <article key={problem.id} className="question-card">
                <div className="question-card-left">
                  <div className="question-card-top">
                    <span className={`difficulty-badge ${difficultyClass(problem.difficulty)}`}>
                      {difficultyLabel(problem.difficulty)}
                    </span>
                    <span className="question-order">Q#{problem.order_index}</span>
                    {isSolved && (
                      <span className="question-chip solved">
                        <CheckCircle2 size={13} />
                        Solved
                      </span>
                    )}
                    {isRecommended && (
                      <span className="question-chip recommended">
                        <Compass size={13} />
                        Recommended
                      </span>
                    )}
                  </div>
                  <h3>{problem.title}</h3>
                  <p>
                    {problem.concept_id ? `Concept: ${problem.concept_id}` : "Concept: General"}
                  </p>
                </div>
                <button
                  className="question-select-btn"
                  onClick={() => onSelectProblem(problem.id)}
                >
                  {isSolved ? "Review Challenge" : "Solve Challenge"}
                </button>
              </article>
            );
          })}

          {filteredProblems.length === 0 && (
            <div className="question-empty">
              No questions match your current filters.
            </div>
          )}
        </div>
      </div>

      <aside className="question-bank-filters">
        <h4>Status</h4>
        <label className="question-filter">
          <input
            type="checkbox"
            checked={showSolved}
            onChange={(event) => setShowSolved(event.target.checked)}
          />
          <span>Solved</span>
        </label>
        <label className="question-filter">
          <input
            type="checkbox"
            checked={showUnsolved}
            onChange={(event) => setShowUnsolved(event.target.checked)}
          />
          <span>Unsolved</span>
        </label>

        <h4>Difficulty</h4>
        {difficultyOptions.map((difficulty) => (
          <label key={difficulty} className="question-filter">
            <input
              type="checkbox"
              checked={difficultyFilters.includes(difficulty)}
              onChange={() => toggleDifficulty(difficulty)}
            />
            <span>{difficultyLabel(difficulty)}</span>
          </label>
        ))}
      </aside>
    </div>
  );
}

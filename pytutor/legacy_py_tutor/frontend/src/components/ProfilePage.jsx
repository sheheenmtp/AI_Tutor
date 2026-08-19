import { useMemo } from "react";
import { BookOpenCheck, Compass, Trophy, Target } from "lucide-react";

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

const levelLabel = (value = "") => {
  const normalized = (value || "beginner").toLowerCase().trim().replace(/\s+/g, "_");
  return normalized
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
};

export default function ProfilePage({
  user,
  progress,
  problems,
  solvedProblems,
  onOpenQuestionBank,
  onOpenRecommended,
}) {
  const solvedSet = useMemo(() => new Set(solvedProblems || []), [solvedProblems]);

  const totalProblems = problems.length;
  const solvedCount = solvedProblems.length;
  const unsolvedCount = Math.max(totalProblems - solvedCount, 0);
  const completion = totalProblems > 0 ? Math.round((solvedCount / totalProblems) * 100) : 0;

  const joinedOn = user?.created_at
    ? new Date(user.created_at).toLocaleDateString()
    : "Unknown";

  const difficultyBreakdown = useMemo(() => {
    const bucket = {};
    for (const problem of problems) {
      const key = canonicalDifficulty(problem.difficulty || "");
      if (!bucket[key]) {
        bucket[key] = { key, total: 0, solved: 0 };
      }
      bucket[key].total += 1;
      if (solvedSet.has(problem.id)) {
        bucket[key].solved += 1;
      }
    }
    return Object.values(bucket).sort((a, b) => a.key.localeCompare(b.key));
  }, [problems, solvedSet]);

  const recommended = progress?.next_problem ?? null;

  return (
    <div className="profile-page">
      <section className="profile-hero">
        <div className="profile-avatar">
          {(user?.username || "U").slice(0, 1).toUpperCase()}
        </div>
        <div className="profile-hero-content">
          <h2>{user?.username || "Learner"}</h2>
          <p>Level: {levelLabel(user?.current_level)}</p>
          <p>Joined: {joinedOn}</p>
        </div>
      </section>

      <section className="profile-kpis">
        <article className="profile-kpi-card">
          <div className="profile-kpi-title">
            <BookOpenCheck size={16} />
            Solved
          </div>
          <div className="profile-kpi-value">{solvedCount}</div>
        </article>

        <article className="profile-kpi-card">
          <div className="profile-kpi-title">
            <Target size={16} />
            Completion
          </div>
          <div className="profile-kpi-value">{completion}%</div>
        </article>

        <article className="profile-kpi-card">
          <div className="profile-kpi-title">
            <Trophy size={16} />
            Total Score
          </div>
          <div className="profile-kpi-value">{user?.total_score ?? 0}</div>
        </article>
      </section>

      <section className="profile-panels">
        <article className="profile-panel">
          <h3>Learning Overview</h3>
          <div className="profile-row">
            <span>Total Questions</span>
            <strong>{totalProblems}</strong>
          </div>
          <div className="profile-row">
            <span>Solved</span>
            <strong>{solvedCount}</strong>
          </div>
          <div className="profile-row">
            <span>Unsolved</span>
            <strong>{unsolvedCount}</strong>
          </div>
          <div className="profile-row">
            <span>Current Level</span>
            <strong>{levelLabel(user?.current_level)}</strong>
          </div>
        </article>

        <article className="profile-panel">
          <h3>Next Recommendation</h3>
          {recommended ? (
            <>
              <div className="profile-row">
                <span>Question</span>
                <strong>{recommended.title}</strong>
              </div>
              <div className="profile-row">
                <span>Order</span>
                <strong>Q#{recommended.order_index}</strong>
              </div>
              <button className="profile-action-btn" onClick={onOpenRecommended}>
                <Compass size={15} />
                Open Recommended
              </button>
            </>
          ) : (
            <p className="profile-muted">No recommendation available right now.</p>
          )}

          <button className="profile-action-btn ghost" onClick={onOpenQuestionBank}>
            Open Question Bank
          </button>
        </article>
      </section>

      <section className="profile-panel">
        <h3>Difficulty Progress</h3>
        <div className="profile-difficulty-list">
          {difficultyBreakdown.map((item) => {
            const pct = item.total > 0 ? Math.round((item.solved / item.total) * 100) : 0;
            return (
              <div key={item.key} className="profile-difficulty-item">
                <div className="profile-row">
                  <span>{difficultyLabel(item.key)}</span>
                  <strong>{item.solved}/{item.total}</strong>
                </div>
                <div className="profile-progress-track">
                  <div className="profile-progress-fill" style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

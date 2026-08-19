import { marked } from "marked";
import { useEffect, useMemo, useState } from "react";

function estimateReadTime(text) {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.ceil(words / 180));
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

function normalizeLessonMarkdown(content) {
  const lines = content.split("\n");
  const output = [];

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];

    if (line.trim() === "bash") {
      const commandLines = [];
      let cursor = index + 1;

      while (cursor < lines.length && lines[cursor].trim()) {
        commandLines.push(lines[cursor]);
        cursor += 1;
      }

      if (commandLines.length > 0) {
        output.push("```bash");
        output.push(...commandLines);
        output.push("```");
        index = cursor - 1;
        continue;
      }
    }

    output.push(line);
  }

  return output.join("\n");
}

function decorateLessonHtml(markdown) {
  const parser = new DOMParser();
  const rawHtml = marked.parse(markdown);
  const document = parser.parseFromString(`<div>${rawHtml}</div>`, "text/html");
  const root = document.body.firstElementChild;
  const headings = [];
  const slugCounts = new Map();

  if (!root) {
    return { html: "", headings: [] };
  }

  root.querySelectorAll("h2, h3").forEach((heading) => {
    const baseSlug = slugify(heading.textContent || "section") || "section";
    const count = slugCounts.get(baseSlug) || 0;
    const id = count === 0 ? baseSlug : `${baseSlug}-${count + 1}`;

    slugCounts.set(baseSlug, count + 1);
    heading.id = id;
    headings.push({
      id,
      title: heading.textContent || "Section",
      depth: Number(heading.tagName.slice(1)),
    });
  });

  root.querySelectorAll("pre").forEach((block) => {
    const code = block.querySelector("code");
    if (code?.className.includes("language-bash")) {
      block.classList.add("command-callout");
    }
  });

  const definitionPattern = /^(A useful summary is:|A good short definition is:|A simple definition is:|Simple definition|So remember:|Key point)/i;
  const warningPattern = /(cannot directly|must ask|should not|damage the whole|protect(?:ed)?|permission checks|boundary)/i;
  let sectionCalloutCount = 0;

  Array.from(root.children).forEach((element) => {
    if (/^H[23]$/.test(element.tagName)) {
      sectionCalloutCount = 0;
      return;
    }

    if (element.tagName !== "P" || sectionCalloutCount >= 2) {
      return;
    }

    const text = element.textContent?.trim() || "";
    let tone = "";
    let label = "";

    if (definitionPattern.test(text)) {
      tone = "definition";
      label = "Definition";
    } else if (warningPattern.test(text)) {
      tone = "warning";
      label = "Important";
    }

    if (!tone) {
      return;
    }

    const callout = document.createElement("div");
    callout.className = `lesson-callout ${tone}`;

    const calloutLabel = document.createElement("div");
    calloutLabel.className = "lesson-callout-label";
    calloutLabel.textContent = label;

    const calloutBody = document.createElement("p");
    calloutBody.textContent = text;

    callout.append(calloutLabel, calloutBody);
    element.replaceWith(callout);
    sectionCalloutCount += 1;
  });

  return {
    html: root.innerHTML,
    headings,
  };
}

function ClockIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 7.5v5l3 1.8" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

export default function LearningPage({
  concept,
  onStartQuiz,
  onRunBash,
  adaptiveMessage = "",
  previousLesson = null,
  nextLesson = null,
  onPreviousLesson,
  onNextLesson,
  onHome,
}) {
  const readTime = estimateReadTime(concept.content || "");
  const [activeHeading, setActiveHeading] = useState("");
  const practiceExercise = concept.practice_exercises?.[0] || null;
  const [bashCode, setBashCode] = useState(practiceExercise?.starter_code || "");
  const [bashResult, setBashResult] = useState(null);
  const [bashError, setBashError] = useState("");
  const [bashRunning, setBashRunning] = useState(false);
  const normalizedContent = useMemo(() => normalizeLessonMarkdown(concept.content || ""), [concept.content]);
  const lessonDocument = useMemo(() => decorateLessonHtml(normalizedContent), [normalizedContent]);
  const tocItems = useMemo(() => {
    const items = [
      {
        id: "lesson-content",
        title: "Lesson",
        depth: 2,
        kind: "section",
      },
      ...lessonDocument.headings.map((heading) => ({
        ...heading,
        kind: "heading",
      })),
    ];

    if (practiceExercise) {
      items.push({
        id: "practice",
        title: "Practice",
        depth: 2,
        kind: "section",
      });
    }

    items.push({
      id: "quiz-check",
      title: "Quiz",
      depth: 2,
      kind: "section",
    });

    return items;
  }, [lessonDocument.headings, practiceExercise]);

  useEffect(() => {
    setBashCode(practiceExercise?.starter_code || "");
    setBashResult(null);
    setBashError("");
  }, [concept.lesson_id, practiceExercise?.id, practiceExercise?.starter_code]);

  useEffect(() => {
    if (!tocItems.length) {
      setActiveHeading("");
      return undefined;
    }

    const headingElements = tocItems
      .map((item) => document.getElementById(item.id))
      .filter(Boolean);

    if (!headingElements.length) {
      setActiveHeading(tocItems[0].id);
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((left, right) => left.boundingClientRect.top - right.boundingClientRect.top);

        if (visible.length > 0) {
          setActiveHeading(visible[0].target.id);
        }
      },
      {
        rootMargin: "-20% 0px -65% 0px",
        threshold: [0, 0.4, 1],
      }
    );

    headingElements.forEach((heading) => observer.observe(heading));
    setActiveHeading(tocItems[0].id);

    return () => observer.disconnect();
  }, [tocItems]);

  const runBash = async () => {
    if (!onRunBash || bashRunning) return;
    setBashRunning(true);
    setBashError("");
    setBashResult(null);

    try {
      const result = await onRunBash({ exerciseId: practiceExercise.id, sourceCode: bashCode });
      setBashResult(result);
    } catch (err) {
      setBashError(err.message || "Unable to run Bash code.");
    } finally {
      setBashRunning(false);
    }
  };

  const navigateToHeading = (event, headingId) => {
    event.preventDefault();
    const heading = document.getElementById(headingId);
    if (!heading) return;

    const nextUrl = new URL(window.location.href);
    nextUrl.hash = headingId;
    window.history.replaceState(window.history.state, "", nextUrl);
    heading.scrollIntoView({ behavior: "smooth", block: "start" });
    setActiveHeading(headingId);
  };

  const bashOutput = bashResult?.stdout || bashResult?.stderr || bashResult?.compile_output || bashResult?.message || "";

  return (
    <>
      <section className="lesson-action-bar" aria-label="Lesson navigation">
        <button className="btn" type="button" onClick={onHome}>
          Home
        </button>
        <button className="btn" type="button" onClick={onPreviousLesson} disabled={!previousLesson}>
          Back
        </button>
      </section>

      {adaptiveMessage && (
        <section className="section">
          <div className="feedback-panel lesson-feedback" role="status">
            <p>{adaptiveMessage}</p>
          </div>
        </section>
      )}

      <section className="banner-section">
        <div className="banner-shell">
          <div className="banner-layout">
            <div className="banner-copy">
              <h1 className="banner-title">{concept.title}</h1>
              <p className="banner-sub">
                {concept.objective ||
                  "Read the lesson first, then move into the check-in quiz when the idea feels clear enough to explain back in your own words."}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="lesson-meta-row">
          <div className="reading-pill">
            <ClockIcon />
            <span>{readTime} min read</span>
          </div>
        </div>
        <div className="lesson-layout">
          <div className="lesson-main-column">
            <div className="section-label">Lesson</div>
            <article className="lesson-panel" id="lesson-content">
              {lessonDocument.html ? (
                <div
                  className="lesson-markdown"
                  dangerouslySetInnerHTML={{ __html: lessonDocument.html }}
                />
              ) : (
                <div className="empty-state compact" role="status">
                  <strong>Lesson content is unavailable</strong>
                  <span>Try returning to the course and opening this lesson again.</span>
                </div>
              )}
            </article>

            {practiceExercise && (
              <section
                className="bash-practice-panel"
                id="practice"
                aria-busy={bashRunning}
                aria-label="Bash practice runner"
              >
                <div className="bash-practice-head">
                  <div>
                    <div className="section-label bash-label">Practice</div>
                    <h3>{practiceExercise.title}</h3>
                    <p>{practiceExercise.prompt}</p>
                  </div>
                  {bashResult?.status?.description && (
                    <span className={`bash-status ${bashResult.passed ? "passed" : ""}`}>
                      {bashResult.passed ? "Passed" : bashResult.status.description}
                    </span>
                  )}
                </div>
                <textarea
                  className="bash-editor"
                  value={bashCode}
                  onChange={(event) => setBashCode(event.target.value)}
                  aria-label={`Bash code for ${practiceExercise.title}`}
                  spellCheck="false"
                />
                <div className="bash-exercise-meta">
                  <span>Allowed: {practiceExercise.allowed_commands.join(", ")}</span>
                  {practiceExercise.expected_output && <span>Expected: {practiceExercise.expected_output}</span>}
                </div>
                <div className="bash-actions">
                  <button className="btn btn-primary" type="button" onClick={runBash} disabled={bashRunning}>
                    {bashRunning ? "Running..." : "Run Bash"}
                  </button>
                  {bashResult?.time && <span>{bashResult.time}s</span>}
                </div>
                {(bashOutput || bashError) && (
                  <pre
                    className={`bash-output ${bashError ? "error" : ""}`}
                    role={bashError ? "alert" : "status"}
                    aria-live="polite"
                  >
                    {bashError || bashOutput}
                  </pre>
                )}
              </section>
            )}

            <div className="lesson-nav">
              <button
                className="lesson-nav-card"
                type="button"
                onClick={onPreviousLesson}
                disabled={!previousLesson}
                aria-label={previousLesson ? `Previous lesson: ${previousLesson.title}` : "No previous lesson"}
              >
                <span className="lesson-nav-direction">Previous</span>
                <strong>{previousLesson ? previousLesson.title : "Start of module"}</strong>
              </button>

              <button
                className="lesson-nav-card lesson-nav-card-primary"
                type="button"
                onClick={onNextLesson}
                disabled={!nextLesson || nextLesson.locked}
                aria-label={nextLesson ? `Next lesson: ${nextLesson.title}` : "No next lesson"}
              >
                <span className="lesson-nav-direction">Next</span>
                <strong>{nextLesson ? nextLesson.title : "No next topic yet"}</strong>
                <span className="lesson-nav-preview">
                  {nextLesson ? `Up next: ${nextLesson.title}` : "You are at the end of this sequence."}
                </span>
              </button>
            </div>

            <div className="cta-section lesson-cta" id="quiz-check">
              <div className="cta-text">
                <h3 className="cta-title">Ready to check understanding?</h3>
                <p className="cta-sub">Continue when the lesson feels clear enough to try.</p>
              </div>
              <div className="cta-actions">
                <button className="btn btn-primary" type="button" onClick={onStartQuiz}>Start quiz</button>
              </div>
            </div>
          </div>

          <aside className="toc-panel">
            <div className="toc-label">On this page</div>
            <nav className="toc-links" aria-label="Lesson table of contents">
              {tocItems.map((heading) => (
                <a
                  key={heading.id}
                  className={`toc-link ${activeHeading === heading.id ? "active" : ""} ${heading.depth === 3 ? "subhead" : ""} ${heading.kind === "section" ? "checkpoint" : ""}`}
                  href={`#${heading.id}`}
                  onClick={(event) => navigateToHeading(event, heading.id)}
                >
                  {heading.title}
                </a>
              ))}
            </nav>
          </aside>
        </div>
      </section>
    </>
  );
}

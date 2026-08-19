import { useEffect, useMemo, useRef, useState } from "react";

export default function QuizPage({
  concept,
  questions,
  onSubmit,
  onCancel,
  questionNumberStart = 1,
  submitting = false,
  error = "",
  retryPrompt = null,
  onRetryQuestions,
  onReviewLesson,
}) {
  const [selected, setSelected] = useState({});
  const quizRef = useRef(null);

  useEffect(() => {
    setSelected({});
    quizRef.current?.focus();
  }, [questions, retryPrompt]);

  const canSubmit = useMemo(
    () => questions.length > 0 && Object.keys(selected).length === questions.length,
    [questions.length, selected]
  );

  const handleSubmit = (event) => {
    event.preventDefault();
    const answers = questions.map((question) => ({
      question_id: question.question_id,
      selected: selected[question.question_id] || "",
    }));
    onSubmit(answers);
  };

  return (
    <section
      className="quiz-shell section"
      ref={quizRef}
      tabIndex="-1"
      aria-busy={submitting}
    >
      <div className="quiz-head">
        <div>
          <div className="quiz-kicker">Check understanding</div>
          <h2 id="quiz-title">{concept.title}</h2>
        </div>
        <button className="icon-button quiz-close" type="button" onClick={onCancel} disabled={submitting} aria-label="Close quiz">
          ×
        </button>
      </div>

      {error && <div className="error-box quiz-error" role="alert">{error}</div>}

      {retryPrompt ? (
        <div className="quiz-choice-panel">
          <p className="quiz-choice-message">{retryPrompt.message}</p>
          <div className="quiz-actions quiz-choice-actions">
            <button className="btn" type="button" onClick={onReviewLesson} disabled={submitting}>
              {submitting ? "Working..." : retryPrompt.review_label}
            </button>
            <button className="btn btn-primary" type="button" onClick={onRetryQuestions} disabled={submitting}>
              {submitting ? "Checking..." : retryPrompt.retry_label}
            </button>
          </div>
        </div>
      ) : (
      <form onSubmit={handleSubmit}>
        <div className="quiz-progress">
          <span>
            {questions.length === 1
              ? `Question ${questionNumberStart}`
              : `Questions ${questionNumberStart}-${questionNumberStart + questions.length - 1}`}
          </span>
          <div className="progress-track">
            <div className="progress-fill quiz-progress-fill" />
          </div>
        </div>

        {questions.map((question, index) => (
          <div className="quiz-question" key={question.question_id}>
            <h3 id={`quiz-question-${question.question_id}`}>
              Question {questionNumberStart + index}. {question.question}
            </h3>
            <div className="quiz-options" role="radiogroup" aria-labelledby={`quiz-question-${question.question_id}`}>
              {question.options.map((option, optionIndex) => {
                const isSelected = selected[question.question_id] === option;
                return (
                  <label className={`quiz-option ${isSelected ? "selected" : ""}`} key={option}>
                    <input
                      type="radio"
                      name={`question-${question.question_id}`}
                      checked={isSelected}
                      onChange={() => setSelected((current) => ({
                        ...current,
                        [question.question_id]: option,
                      }))}
                    />
                    <span className="option-letter">{String.fromCharCode(65 + optionIndex)}</span>
                    <span>{option}</span>
                  </label>
                );
              })}
            </div>
          </div>
        ))}

        <div className="quiz-actions">
          <button className="btn" type="button" onClick={onCancel} disabled={submitting}>Back to lesson</button>
          <button className="btn btn-primary" type="submit" disabled={!canSubmit || submitting}>
            {submitting ? "Checking..." : "Continue"}
          </button>
        </div>
      </form>
      )}
    </section>
  );
}

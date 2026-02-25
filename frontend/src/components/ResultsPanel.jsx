import { useState } from 'react';
import { Terminal, CheckCircle2, XCircle, AlertCircle, Trophy, Sparkles, Play, X, Copy, Maximize2 } from 'lucide-react';

export default function ResultsPanel({
  submissionResult,
  runOutput,
  aiFeedback
}) {
  const [activeTab, setActiveTab] = useState('output');
  const [copied, setCopied] = useState(false);

  // Determine which tabs should be visible
  const hasOutput = runOutput && !submissionResult;
  const hasSubmission = submissionResult;
  const hasAIFeedback = aiFeedback;

  // Auto-select appropriate tab based on content
  const getVisibleTabs = () => {
    const tabs = [];
    if (hasOutput) tabs.push({ id: 'output', label: 'Output', icon: Play });
    if (hasSubmission) {
      tabs.push({ id: 'testcases', label: 'Test Cases', icon: CheckCircle2 });
      tabs.push({ id: 'summary', label: 'Summary', icon: Trophy });
    }
    if (hasAIFeedback) tabs.push({ id: 'ai', label: 'AI Feedback', icon: Sparkles });
    return tabs;
  };

  const visibleTabs = getVisibleTabs();

  // If no active tab is valid, select first available
  if (visibleTabs.length > 0 && !visibleTabs.find(t => t.id === activeTab)) {
    setActiveTab(visibleTabs[0].id);
  }

  const handleCopy = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!submissionResult && !runOutput && !aiFeedback) {
    return (
      <div className="results-container">
        <div className="empty-state">
          <div className="empty-icon">
            <Terminal size={40} />
          </div>
          <h3>No Results Yet</h3>
          <p>Run or submit your code to see the output</p>
        </div>
      </div>
    );
  }

  return (
    <div className="results-container">
      {/* Header with Tabs */}
      <div className="results-header">
        <div className="results-tabs">
          {visibleTabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            let tabClass = 'result-tab';
            if (isActive) tabClass += ' active';

            // Add success/error styling for test cases tab
            if (tab.id === 'testcases' && submissionResult) {
              tabClass += submissionResult.all_passed ? ' success' : ' error';
            }

            return (
              <button
                key={tab.id}
                className={tabClass}
                onClick={() => setActiveTab(tab.id)}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
        <div className="results-toolbar">
          {activeTab === 'output' && runOutput && (
            <button
              className="toolbar-btn"
              onClick={() => handleCopy(runOutput)}
              title="Copy output"
            >
              <Copy size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Content Area */}
      <div className="results-content">
        {/* Quick Run Output */}
        {hasOutput && activeTab === 'output' && (
          <div className="result-section">
            <div className="result-section-header">
              <div className="section-title">
                <Play size={14} />
                <span>Console Output</span>
              </div>
            </div>
            <div className="result-section-body">
              <pre className="output-box">{runOutput}</pre>
            </div>
          </div>
        )}

        {/* Summary */}
        {hasSubmission && activeTab === 'summary' && (
          <div className={`result-summary ${submissionResult.all_passed ? 'success' : 'partial'}`}>
            <div className="summary-left">
              <div className="summary-icon">
                {submissionResult.all_passed ? (
                  <Trophy size={28} />
                ) : (
                  <AlertCircle size={28} />
                )}
              </div>
              <div className="summary-text">
                <h2>
                  {submissionResult.all_passed ? 'Accepted' : 'Wrong Answer'}
                </h2>
                <p className="summary-subtitle">
                  {submissionResult.passed_tests} / {submissionResult.total_tests} test cases passed
                </p>
              </div>
            </div>
            <div className="summary-right">
              <div className="score-badge">
                <div className="score-label">Score</div>
                <div className="score-value">
                  {submissionResult.score} / {submissionResult.max_score}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Test Cases */}
        {hasSubmission && activeTab === 'testcases' && (
          <div className="result-section">
            <div className="result-section-header">
              <div className="section-title">
                <CheckCircle2 size={14} />
                <span>Test Results</span>
              </div>
              <span className="test-count">
                {submissionResult.passed_tests}/{submissionResult.total_tests} passed
              </span>
            </div>
            <div className="result-section-body">
              <div className="test-results-list">
                {submissionResult.test_results.map((test, idx) => (
                  <div
                    key={idx}
                    className={`test-result-item ${test.passed ? 'passed' : 'failed'}`}
                  >
                    <div className="test-item-header">
                      <div className="test-item-left">
                        <div className="test-status-icon">
                          {test.passed ? (
                            <CheckCircle2 size={14} />
                          ) : (
                            <XCircle size={14} />
                          )}
                        </div>
                        <span className="test-name">
                          {test.is_sample ? `Sample ${idx + 1}` : `Hidden ${idx + 1}`}
                        </span>
                      </div>
                      <span className={`test-status-label ${test.passed ? 'passed' : 'failed'}`}>
                        {test.passed ? 'Passed' : 'Failed'}
                      </span>
                    </div>

                    {test.is_sample && (
                      <div className="test-details">
                        <div className="test-detail-row">
                          <span className="detail-label">Expected:</span>
                          <pre className="detail-value">{test.expected}</pre>
                        </div>
                        <div className="test-detail-row">
                          <span className="detail-label">Output:</span>
                          <pre className={`detail-value ${test.passed ? 'success' : 'error'}`}>
                            {test.actual || test.error || 'No output'}
                          </pre>
                        </div>
                      </div>
                    )}

                    {test.error && (
                      <div className="test-error">
                        <strong>Error:</strong> {test.error}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* AI Feedback */}
        {hasAIFeedback && activeTab === 'ai' && (
          <div className="result-section ai-section">
            <div className="result-section-header">
              <div className="section-title">
                <Sparkles size={14} />
                <span>AI Tutor Feedback</span>
              </div>
            </div>
            <div className="result-section-body">
              <div className="ai-feedback-content">
                {aiFeedback}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

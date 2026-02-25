import Editor from "@monaco-editor/react";
import { Code2, Send, Sparkles, CheckSquare, Loader2 } from 'lucide-react';
import { useEffect } from 'react';

export default function CodeEditor({
  code,
  setCode,
  onRun,
  onValidate,
  onSubmit,
  onGetHint,
  loading,
  hasOutput,
  theme,
  currentProblemId
}) {
  useEffect(() => {
    if (currentProblemId) {
      const savedCode = localStorage.getItem(`code-save-${currentProblemId}`);
      if (savedCode && !code) {
        setCode(savedCode);
      }
    }
  }, [currentProblemId]);

  useEffect(() => {
    if (currentProblemId && code !== undefined) {
      localStorage.setItem(`code-save-${currentProblemId}`, code);
    }
  }, [code, currentProblemId]);

  return (
    <div className="editor-container">
      <div className="editor-header">
        <div className="editor-header-left">
          <Code2 size={18} />
          <h3>Solution</h3>
          <span className="language-badge">Python 3</span>
        </div>
        
        <div className="editor-actions">
          <button
            onClick={onValidate}
            className="btn btn-warning"
            disabled={loading}
            title="Check against all test cases"
          >
            <CheckSquare size={16} />
            Check
          </button>

          {hasOutput && (
            <button 
              onClick={onGetHint} 
              className="btn btn-purple"
              disabled={loading}
              title="Get AI assistance"
            >
              <Sparkles size={16} />
              Hint
            </button>
          )}

          <button 
            onClick={onSubmit} 
            className="btn btn-success"
            disabled={loading}
            title="Submit final solution"
          >
            <Send size={16} />
            Submit
          </button>
        </div>
      </div>
      
      <div className="editor-wrapper">
        <Editor
          height="100%"
          language="python"
          theme={theme === 'dark' ? 'vs-dark' : 'light'}
          value={code}
          onChange={setCode}
          options={{ 
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
            fontLigatures: true,
            bracketPairColorization: { enabled: true },
            smoothScrolling: true,
            cursorBlinking: 'smooth',
            cursorSmoothCaretAnimation: 'on',
            renderLineHighlight: 'all',
            padding: { top: 16, bottom: 16 },
          }}
        />
      </div>
    </div>
  );
}
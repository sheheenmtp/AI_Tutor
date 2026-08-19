import { marked } from "marked";
import { useEffect, useMemo, useRef, useState } from "react";

function sanitizeHtml(html) {
  const parser = new DOMParser();
  const document = parser.parseFromString(`<div>${html}</div>`, "text/html");
  const root = document.body.firstElementChild;

  if (!root) return "";

  root.querySelectorAll("script, style, iframe, object, embed, link, meta").forEach((element) => element.remove());
  root.querySelectorAll("*").forEach((element) => {
    Array.from(element.attributes).forEach((attribute) => {
      const name = attribute.name.toLowerCase();
      const value = attribute.value.trim().toLowerCase();
      if (name.startsWith("on") || value.startsWith("javascript:")) {
        element.removeAttribute(attribute.name);
      }
    });
  });

  return root.innerHTML;
}

function renderTeacherMarkdown(content) {
  const html = marked.parse(content || "", {
    breaks: true,
    gfm: true,
  });
  return sanitizeHtml(html);
}

function TeacherIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 7.4 12 3l8 4.4-8 4.4L4 7.4Z" fill="none" stroke="currentColor" strokeLinejoin="round" strokeWidth="1.8" />
      <path d="M7 10v4.2c0 1.8 2.2 3.1 5 3.1s5-1.3 5-3.1V10" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.8" />
    </svg>
  );
}

export default function TeacherChat({ concept, activeLab = null, onAskTeacher }) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState([]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef(null);
  const draftRef = useRef(null);
  const fabRef = useRef(null);

  const greeting = useMemo(() => {
    const target = activeLab?.title || concept?.title || "this lesson";
    return `Hi, I am your Linux teacher. Ask me anything about ${target}, and I will guide you step by step.`;
  }, [activeLab?.title, concept?.title]);

  useEffect(() => {
    setMessages([{ role: "assistant", content: greeting }]);
    setDraft("");
    setError("");
  }, [concept?.lesson_id, activeLab?.id, greeting]);

  useEffect(() => {
    if (open) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, open]);

  useEffect(() => {
    if (open) {
      draftRef.current?.focus();
    }
  }, [open]);

  const closeChat = () => {
    setOpen(false);
    window.requestAnimationFrame(() => fabRef.current?.focus());
  };

  const sendMessage = async (event) => {
    event.preventDefault();
    const message = draft.trim();
    if (!message || sending) return;

    const nextMessages = [...messages, { role: "user", content: message }];
    setMessages(nextMessages);
    setDraft("");
    setError("");
    setSending(true);
    const assistantIndex = nextMessages.length;
    setMessages([...nextMessages, { role: "assistant", content: "" }]);

    try {
      await onAskTeacher({
        message,
        history: messages,
        onToken: (chunk) => {
          setMessages((current) =>
            current.map((item, index) =>
              index === assistantIndex ? { ...item, content: `${item.content}${chunk}` } : item
            )
          );
        },
      });
    } catch (err) {
      setError(err.message || "Teacher is not available right now.");
      setMessages(nextMessages);
    } finally {
      setSending(false);
    }
  };

  const handleDraftKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  };

  if (!concept) return null;

  return (
    <div className={`teacher-chat ${open ? "open" : ""}`}>
      {open && (
        <section
          className="teacher-chat-panel"
          id="teacher-chat-panel"
          role="dialog"
          aria-labelledby="teacher-chat-title"
          aria-busy={sending}
        >
          <header className="teacher-chat-header">
            <div className="teacher-chat-avatar">
              <TeacherIcon />
            </div>
            <div>
              <h3 id="teacher-chat-title">Ask teacher</h3>
              <p>{activeLab ? "Lab help" : "Lesson help"}</p>
            </div>
            <button className="icon-button teacher-chat-close" type="button" onClick={closeChat} aria-label="Close teacher chat">
              ×
            </button>
          </header>

          <div className="teacher-chat-messages" aria-live="polite">
            {messages.map((item, index) => (
              <div className={`teacher-message ${item.role}`} key={`${item.role}-${index}`}>
                {item.role === "assistant" ? (
                  <div
                    className="teacher-message-content"
                    dangerouslySetInnerHTML={{ __html: renderTeacherMarkdown(item.content || "Thinking...") }}
                  />
                ) : (
                  item.content
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {error && <div className="teacher-chat-error" role="alert">{error}</div>}

          <form className="teacher-chat-form" onSubmit={sendMessage}>
            <textarea
              ref={draftRef}
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleDraftKeyDown}
              placeholder="Ask for a hint or explanation..."
              rows="2"
            />
            <button className="btn btn-primary" type="submit" disabled={sending || !draft.trim()}>
              {sending ? "Sending..." : "Send"}
            </button>
          </form>
        </section>
      )}

      <button
        className="teacher-chat-fab"
        ref={fabRef}
        type="button"
        aria-controls="teacher-chat-panel"
        aria-expanded={open}
        aria-label={open ? "Close teacher chat" : "Open teacher chat"}
        onClick={() => setOpen((current) => !current)}
      >
        <TeacherIcon />
        <span>Ask teacher</span>
      </button>
    </div>
  );
}

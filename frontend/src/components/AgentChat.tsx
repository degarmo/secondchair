import { CornerDownLeft, Send } from "lucide-react";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";

import { askInterview, InterviewError, type ChatTurn } from "../api";
import { CONTACT } from "../content";
import styles from "./AgentChat.module.css";

const QUESTION_MAX_LENGTH = 500;

interface Message extends ChatTurn {
  id: number;
}

interface Failure {
  kind: "throttled" | "other";
  message: string;
}

interface AgentChatProps {
  starters: readonly string[];
}

let nextId = 0;

export default function AgentChat({ starters }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [failure, setFailure] = useState<Failure | null>(null);
  // Session id lives in React state only. Nothing is written to storage.
  const [sessionId, setSessionId] = useState<string | null>(null);

  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    const node = transcriptRef.current;
    if (node) {
      node.scrollTop = node.scrollHeight;
    }
  }, [messages, pending]);

  const send = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || pending) {
      return;
    }

    const history: ChatTurn[] = messages.map(({ role, content }) => ({
      role,
      content,
    }));

    const asked: Message = { id: nextId++, role: "user", content: trimmed };
    setMessages((current) => [...current, asked]);
    setDraft("");
    setFailure(null);
    setPending(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await askInterview(
        trimmed,
        history,
        sessionId,
        controller.signal,
      );
      setSessionId(result.session_id);
      setMessages((current) => [
        ...current,
        { id: nextId++, role: "assistant", content: result.answer },
      ]);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }

      // Take the question back out of the transcript and put it back in the
      // box, so nothing is lost and the thread stays coherent.
      setMessages((current) => current.filter((message) => message.id !== asked.id));
      setDraft(trimmed);

      if (error instanceof InterviewError && error.kind === "throttled") {
        setFailure({ kind: "throttled", message: error.message });
      } else if (error instanceof InterviewError) {
        setFailure({ kind: "other", message: error.message });
      } else {
        setFailure({
          kind: "other",
          message: "Something went wrong. Try that again.",
        });
      }
    } finally {
      setPending(false);
      abortRef.current = null;
      inputRef.current?.focus();
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send(draft);
    }
  };

  const remaining = QUESTION_MAX_LENGTH - draft.length;
  const canSend = draft.trim().length > 0 && !pending;

  return (
    <div className={styles.chat}>
      <div
        className={styles.transcript}
        ref={transcriptRef}
        role="log"
        aria-live="polite"
        aria-label="Interview transcript"
      >
        {messages.length === 0 && !pending ? (
          <p className={styles.empty}>
            Ask anything about my background, my work, or what I've shipped.
            Answers come from a knowledge base I wrote, and the agent will tell
            you when something isn't in it.
          </p>
        ) : null}

        {messages.map((message) => (
          <div
            key={message.id}
            className={
              message.role === "user" ? styles.fromVisitor : styles.fromAgent
            }
          >
            <span className={styles.speaker}>
              {message.role === "user" ? "You" : "Cory's agent"}
            </span>
            <div className={styles.bubble}>{message.content}</div>
          </div>
        ))}

        {pending ? (
          <div className={styles.fromAgent}>
            <span className={styles.speaker}>Cory's agent</span>
            <div className={`${styles.bubble} ${styles.typing}`}>
              <span className={styles.dot} />
              <span className={styles.dot} />
              <span className={styles.dot} />
              <span className={styles.srOnly}>Thinking</span>
            </div>
          </div>
        ) : null}
      </div>

      {messages.length === 0 ? (
        <ul className={styles.starters}>
          {starters.map((starter) => (
            <li key={starter}>
              <button
                type="button"
                className={styles.starter}
                onClick={() => void send(starter)}
                disabled={pending}
              >
                {starter}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {failure ? (
        <p className={styles.failure} role="alert">
          {failure.kind === "throttled" ? (
            <>
              Rate limit hit -{" "}
              <a href={`mailto:${CONTACT.email}`}>email Cory instead</a>. He
              answers faster than you'd think.
            </>
          ) : (
            <>
              {failure.message}{" "}
              <a href={`mailto:${CONTACT.email}`}>Or email Cory directly.</a>
            </>
          )}
        </p>
      ) : null}

      <form
        className={styles.composer}
        onSubmit={(event) => {
          event.preventDefault();
          void send(draft);
        }}
      >
        <label className={styles.srOnly} htmlFor="question">
          Your question
        </label>
        <textarea
          id="question"
          ref={inputRef}
          className={styles.input}
          value={draft}
          rows={2}
          maxLength={QUESTION_MAX_LENGTH}
          placeholder="What would you want to ask in a first interview?"
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
        />
        <div className={styles.composerFooter}>
          <span className={styles.hint}>
            <CornerDownLeft size={13} aria-hidden="true" /> to send, Shift +
            Enter for a new line
            {remaining <= 100 ? ` - ${remaining} characters left` : ""}
          </span>
          <button type="submit" className={styles.send} disabled={!canSend}>
            <Send size={16} aria-hidden="true" />
            <span>Send</span>
          </button>
        </div>
      </form>
    </div>
  );
}

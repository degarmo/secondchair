import { useEffect, useRef, type CSSProperties, type ReactNode } from "react";

import { IconButton } from "./core";
import { Icon } from "./Icon";

/*
 * Chat components from the DeGarmo design system export
 * (components/chat/*.jsx).
 *
 * Two things here are additions rather than ports, both drawn in the system's
 * own idiom: a microphone control in ChatInput, and a "Listen" action under an
 * agent message. The export predates the voice feature.
 */

export type ChatRole = "user" | "agent";

export interface ChatMessage {
  id: number;
  role: ChatRole;
  text: string;
  /** Set on stored agent answers; the id the speech endpoint is addressed by. */
  logId?: number;
}

export interface ChatNoticeState {
  variant: "info" | "error" | "limit";
  text: ReactNode;
}

// --- MessageBubble --------------------------------------------------------

function MessageBubble({
  role = "agent",
  children,
  action,
}: {
  role?: ChatRole;
  children: ReactNode;
  action?: ReactNode;
}) {
  const user = role === "user";
  return (
    <div
      className={`message-bubble message-bubble--${role}`}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-2)",
        alignItems: user ? "flex-end" : "flex-start",
      }}
    >
      <span
        style={{
          font: "var(--text-eyebrow)",
          letterSpacing: "var(--tracking-meta)",
          textTransform: "uppercase",
          color: user ? "var(--text-faint)" : "var(--text-accent)",
        }}
      >
        {user ? "You" : "Agent"}
      </span>
      <div
        style={{
          maxWidth: "86%",
          padding: "var(--space-4) var(--space-5)",
          font: "var(--text-base)",
          color: user ? "var(--text-strong)" : "var(--text-body)",
          background: user ? "var(--accent-wash)" : "var(--surface-2)",
          border: `1px solid ${user ? "var(--border-accent)" : "var(--border-subtle)"}`,
          borderRadius: "var(--radius-md)",
          borderTopRightRadius: user ? "var(--radius-xs)" : undefined,
          borderTopLeftRadius: user ? undefined : "var(--radius-xs)",
          whiteSpace: "pre-wrap",
        }}
      >
        {children}
      </div>
      {action}
    </div>
  );
}

// --- TypingIndicator ------------------------------------------------------

function TypingIndicator({ label = "Agent" }: { label?: string }) {
  return (
    <div
      className="typing-indicator"
      role="status"
      aria-live="polite"
      style={{ display: "flex", flexDirection: "column", gap: "var(--space-2)" }}
    >
      <span
        style={{
          font: "var(--text-eyebrow)",
          letterSpacing: "var(--tracking-meta)",
          textTransform: "uppercase",
          color: "var(--text-accent)",
        }}
      >
        {label}
      </span>
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 5,
          padding: "var(--space-4) var(--space-5)",
          width: "fit-content",
          background: "var(--surface-2)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-md)",
          borderTopLeftRadius: "var(--radius-xs)",
        }}
      >
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: "var(--text-muted)",
              animation: "ds-typing 1.4s var(--ease-in-out) infinite",
              animationDelay: `${i * 0.16}s`,
            }}
          />
        ))}
        <span className="ds-visually-hidden">Thinking</span>
      </div>
    </div>
  );
}

// --- StarterChips ---------------------------------------------------------

function Chip({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return (
    <button
      type="button"
      className="starter-chip"
      onClick={onClick}
      style={{
        textAlign: "left",
        padding: "9px 13px",
        font: "var(--text-small)",
        color: "var(--text-muted)",
        background: "transparent",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-pill)",
        cursor: "pointer",
        transition:
          "color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.color = "var(--text-strong)";
        e.currentTarget.style.background = "var(--accent-wash)";
        e.currentTarget.style.borderColor = "var(--border-accent)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.color = "var(--text-muted)";
        e.currentTarget.style.background = "transparent";
        e.currentTarget.style.borderColor = "var(--border-subtle)";
      }}
    >
      {children}
    </button>
  );
}

function StarterChips({
  prompts,
  onPick,
}: {
  prompts: readonly string[];
  onPick: (p: string) => void;
}) {
  return (
    <div
      className="starter-chips"
      style={{ display: "flex", flexWrap: "wrap", gap: "var(--space-2)" }}
    >
      {prompts.map((p) => (
        <Chip key={p} onClick={() => onPick(p)}>
          {p}
        </Chip>
      ))}
    </div>
  );
}

// --- ChatNotice -----------------------------------------------------------

const NOTICE = {
  info: {
    icon: "circle-dot",
    fg: "var(--text-muted)",
    bg: "transparent",
    border: "var(--border-hairline)",
  },
  error: {
    icon: "triangle-alert",
    fg: "var(--danger)",
    bg: "var(--danger-bg)",
    border: "var(--danger)",
  },
  limit: {
    icon: "loader-circle",
    fg: "var(--status-live)",
    bg: "var(--status-live-bg)",
    border: "var(--status-live)",
  },
} as const;

function ChatNotice({
  variant = "info",
  children,
}: {
  variant?: keyof typeof NOTICE;
  children: ReactNode;
}) {
  const s = NOTICE[variant] ?? NOTICE.info;
  return (
    <div
      className={`chat-notice chat-notice--${variant}`}
      role={variant === "error" ? "alert" : undefined}
      style={{
        display: "flex",
        alignItems: "flex-start",
        gap: "var(--space-3)",
        padding: "var(--space-3) var(--space-4)",
        font: "var(--text-small)",
        color: s.fg,
        background: s.bg,
        border: `1px solid ${s.border}`,
        borderRadius: "var(--radius-sm)",
      }}
    >
      <Icon name={s.icon} size={15} style={{ marginTop: 2 }} />
      <span>{children}</span>
    </div>
  );
}

// --- Audio toggle ---------------------------------------------------------

/**
 * Speech is all-or-nothing: one switch in the panel header, rather than a
 * control on every answer. When it is on, answers play as they arrive.
 */
export interface AudioToggleState {
  enabled: boolean;
  /** An answer is being fetched or is playing right now. */
  busy: "loading" | "playing" | null;
  onToggle: () => void;
}

function AudioToggle({ enabled, busy, onToggle }: AudioToggleState) {
  const icon = busy === "loading" ? "loader-circle" : enabled ? "volume-2" : "volume-x";
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={enabled}
      // No aria-label: the visible "Audio on"/"Audio off" is the accessible
      // name, so speaking the label operates the control (WCAG 2.5.3). State
      // is carried by aria-pressed, the rest by the title.
      title={
        enabled
          ? "Answers are read aloud as they arrive"
          : "Read answers aloud as they arrive"
      }
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "4px 10px",
        font: "var(--text-data)",
        letterSpacing: "var(--tracking-meta)",
        textTransform: "uppercase",
        color: enabled ? "var(--text-accent)" : "var(--text-faint)",
        background: "transparent",
        border: `1px solid ${
          enabled ? "var(--border-accent)" : "var(--border-hairline)"
        }`,
        borderRadius: "var(--radius-pill)",
        cursor: "pointer",
        transition:
          "color var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out)",
      }}
    >
      <Icon
        name={icon}
        size={13}
        style={
          busy === "loading"
            ? { animation: "ds-spin 900ms var(--ease-linear) infinite" }
            : busy === "playing"
              ? { animation: "ds-pulse 1.6s var(--ease-in-out) infinite" }
              : undefined
        }
      />
      Audio {enabled ? "on" : "off"}
    </button>
  );
}

// --- ChatInput ------------------------------------------------------------

export interface VoiceState {
  supported: boolean;
  listening: boolean;
  onToggle: () => void;
}

const QUESTION_MAX_LENGTH = 500;

function ChatInput({
  value,
  onChange,
  onSend,
  disabled = false,
  voice,
  placeholder = "Ask a question…",
}: {
  value: string;
  onChange: (v: string) => void;
  onSend: (text: string) => void;
  disabled?: boolean;
  voice?: VoiceState;
  placeholder?: string;
}) {
  const submit = () => {
    if (!disabled && value.trim()) {
      onSend(value.trim());
    }
  };

  return (
    <form
      className="chat-input"
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        padding: "var(--space-2)",
        background: "var(--surface-inset)",
        border: `1px solid ${
          voice?.listening ? "var(--border-accent)" : "var(--border-subtle)"
        }`,
        borderRadius: "var(--radius-md)",
        transition: "border-color var(--dur-fast) var(--ease-out)",
      }}
    >
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        maxLength={QUESTION_MAX_LENGTH}
        placeholder={voice?.listening ? "Listening…" : placeholder}
        aria-label="Ask the interview agent a question"
        style={{
          flex: 1,
          minWidth: 0,
          padding: "10px 12px",
          font: "var(--text-base)",
          color: "var(--text-strong)",
          background: "transparent",
          border: 0,
          outline: "none",
        }}
      />

      {voice?.supported ? (
        <IconButton
          icon={voice.listening ? "square" : "mic"}
          // Stopping submits, same as pausing does — say so, rather than
          // leaving "stop" to imply the question is discarded.
          label={voice.listening ? "Stop and send" : "Ask by voice"}
          variant={voice.listening ? "primary" : "ghost"}
          size="lg"
          pressed={voice.listening}
          disabled={disabled}
          onClick={voice.onToggle}
        />
      ) : null}

      <IconButton
        icon={disabled ? "loader-circle" : "send"}
        label="Send"
        variant="primary"
        size="lg"
        type="submit"
        disabled={disabled || !value.trim()}
      />
    </form>
  );
}

// --- ChatPanel ------------------------------------------------------------

interface ChatPanelProps {
  messages: readonly ChatMessage[];
  draft: string;
  onDraftChange: (v: string) => void;
  onSend: (text: string) => void;
  pending?: boolean;
  error?: ChatNoticeState | null;
  prompts?: readonly string[];
  note?: ReactNode;
  status?: string;
  voice?: VoiceState;
  /** The header audio switch, or null when the site has no voice configured. */
  audio?: AudioToggleState | null;
  style?: CSSProperties;
}

export function ChatPanel({
  messages,
  draft,
  onDraftChange,
  onSend,
  pending = false,
  error = null,
  prompts = [],
  note,
  status = "Agent online",
  voice,
  audio = null,
  style,
}: ChatPanelProps) {
  const scroller = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scroller.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages.length, pending]);

  return (
    <div
      className="chat-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        maxWidth: "var(--container-narrow)",
        marginInline: "auto",
        background: "var(--surface-card)",
        border: "1px solid var(--border-subtle)",
        borderRadius: "var(--radius-lg)",
        boxShadow: "var(--shadow-panel)",
        overflow: "hidden",
        ...style,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3)",
          padding: "var(--space-4) var(--space-5)",
          borderBottom: "1px solid var(--border-hairline)",
          background: "var(--surface-1)",
        }}
      >
        <Icon name="terminal" size={15} style={{ color: "var(--text-accent)" }} />
        <span
          style={{
            font: "var(--text-eyebrow)",
            letterSpacing: "var(--tracking-meta)",
            textTransform: "uppercase",
            color: "var(--text-muted)",
          }}
        >
          Interview Cory
        </span>
        <span style={{ flex: 1 }} />
        {audio ? <AudioToggle {...audio} /> : null}
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            font: "var(--text-data)",
            color: "var(--text-faint)",
          }}
        >
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: "50%",
              background: "var(--green-500)",
              animation: "ds-pulse 3s var(--ease-in-out) infinite",
            }}
          />
          {status}
        </span>
      </div>

      <div
        ref={scroller}
        role="log"
        aria-live="polite"
        aria-label="Interview transcript"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-6)",
          padding: "var(--space-6) var(--space-5)",
          minHeight: 180,
          maxHeight: 420,
          overflowY: "auto",
        }}
      >
        {messages.map((m) => (
          <MessageBubble key={m.id} role={m.role}>
            {m.text}
          </MessageBubble>
        ))}
        {pending ? <TypingIndicator /> : null}
        {error ? <ChatNotice variant={error.variant}>{error.text}</ChatNotice> : null}
      </div>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "var(--space-3)",
          padding: "var(--space-5)",
          borderTop: "1px solid var(--border-hairline)",
          background: "var(--surface-1)",
        }}
      >
        {prompts.length ? <StarterChips prompts={prompts} onPick={onSend} /> : null}
        <ChatInput
          value={draft}
          onChange={onDraftChange}
          onSend={onSend}
          disabled={pending}
          voice={voice}
        />
        {note ? (
          <p style={{ font: "var(--text-small)", color: "var(--text-faint)" }}>{note}</p>
        ) : null}
      </div>
    </div>
  );
}

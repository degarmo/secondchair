import {
  CornerDownLeft,
  Loader2,
  Mic,
  Send,
  Square,
  Volume2,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";

import {
  askInterview,
  fetchAnswerAudio,
  InterviewError,
  type ChatTurn,
} from "../api";
import { CONTACT } from "../content";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";
import styles from "./AgentChat.module.css";

const QUESTION_MAX_LENGTH = 500;

interface Message extends ChatTurn {
  id: number;
  /** Present on agent answers once stored, and only then can they be spoken. */
  logId?: number;
}

interface Failure {
  kind: "throttled" | "other";
  message: string;
}

interface Playback {
  logId: number;
  status: "loading" | "playing";
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
  const [speechAvailable, setSpeechAvailable] = useState(false);
  const [playback, setPlayback] = useState<Playback | null>(null);
  const [playbackError, setPlaybackError] = useState<string | null>(null);

  const transcriptRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Whatever was typed before dictation started; the transcript is appended
  // to it rather than replacing what they had written.
  const draftBaseRef = useRef("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlsRef = useRef(new Map<number, string>());
  const audioAbortRef = useRef<AbortController | null>(null);

  const onTranscript = useCallback((transcript: string, isFinal: boolean) => {
    const base = draftBaseRef.current;
    const combined = base ? `${base} ${transcript}` : transcript;
    setDraft(combined.slice(0, QUESTION_MAX_LENGTH));
    if (isFinal) {
      inputRef.current?.focus();
    }
  }, []);

  const {
    supported: micSupported,
    listening,
    error: micError,
    stop: stopListening,
    start: startListening,
    setError: setMicError,
  } = useSpeechRecognition({ onTranscript });

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    const urls = audioUrlsRef.current;
    return () => {
      audioAbortRef.current?.abort();
      audioRef.current?.pause();
      for (const url of urls.values()) {
        URL.revokeObjectURL(url);
      }
      urls.clear();
    };
  }, []);

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

    if (listening) {
      stopListening();
    }

    const history: ChatTurn[] = messages.map(({ role, content }) => ({
      role,
      content,
    }));

    const asked: Message = { id: nextId++, role: "user", content: trimmed };
    setMessages((current) => [...current, asked]);
    setDraft("");
    draftBaseRef.current = "";
    setFailure(null);
    setMicError(null);
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
      setSpeechAvailable(result.speech_available);
      setMessages((current) => [
        ...current,
        {
          id: nextId++,
          role: "assistant",
          content: result.answer,
          logId: result.log_id,
        },
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

  const stopPlayback = useCallback(() => {
    audioAbortRef.current?.abort();
    audioAbortRef.current = null;
    const audio = audioRef.current;
    if (audio) {
      audio.pause();
      audio.currentTime = 0;
    }
    setPlayback(null);
  }, []);

  const speak = async (logId: number) => {
    if (playback?.logId === logId) {
      stopPlayback();
      return;
    }

    stopPlayback();
    setPlaybackError(null);
    setPlayback({ logId, status: "loading" });

    try {
      let url = audioUrlsRef.current.get(logId);

      if (!url) {
        const controller = new AbortController();
        audioAbortRef.current = controller;
        const blob = await fetchAnswerAudio(logId, controller.signal);
        url = URL.createObjectURL(blob);
        audioUrlsRef.current.set(logId, url);
        audioAbortRef.current = null;
      }

      const audio = audioRef.current;
      if (!audio) {
        return;
      }
      audio.src = url;
      await audio.play();
      setPlayback({ logId, status: "playing" });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setPlayback(null);
      setPlaybackError(
        error instanceof InterviewError
          ? error.message
          : "That answer could not be played.",
      );
    }
  };

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void send(draft);
    }
  };

  const onMicClick = () => {
    if (listening) {
      stopListening();
      return;
    }
    // Anchor the transcript to whatever is already typed.
    draftBaseRef.current = draft.trim();
    startListening();
  };

  const remaining = QUESTION_MAX_LENGTH - draft.length;
  const canSend = draft.trim().length > 0 && !pending;

  return (
    <div className={styles.chat}>
      <audio
        ref={audioRef}
        onEnded={() => setPlayback(null)}
        onError={() => {
          setPlayback(null);
          setPlaybackError("That answer could not be played.");
        }}
        hidden
      />

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
            {micSupported ? " Type it, or use the microphone." : ""}
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

            {message.role === "assistant" &&
            speechAvailable &&
            message.logId !== undefined ? (
              <button
                type="button"
                className={styles.playButton}
                onClick={() => void speak(message.logId as number)}
                aria-label={
                  playback?.logId === message.logId
                    ? "Stop playing this answer"
                    : "Play this answer aloud"
                }
              >
                {playback?.logId === message.logId ? (
                  playback.status === "loading" ? (
                    <>
                      <Loader2 size={14} className={styles.spin} aria-hidden="true" />
                      Loading
                    </>
                  ) : (
                    <>
                      <Square size={14} aria-hidden="true" />
                      Stop
                    </>
                  )
                ) : (
                  <>
                    <Volume2 size={14} aria-hidden="true" />
                    Listen
                  </>
                )}
              </button>
            ) : null}
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

      {micError ? (
        <p className={styles.notice} role="alert">
          {micError}
        </p>
      ) : null}

      {playbackError ? (
        <p className={styles.notice} role="alert">
          {playbackError}
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
          placeholder={
            listening
              ? "Listening..."
              : "What would you want to ask in a first interview?"
          }
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onKeyDown}
        />
        <div className={styles.composerFooter}>
          <span className={styles.hint}>
            {listening ? (
              <>
                <span className={styles.listeningDot} aria-hidden="true" />
                Listening - stop when you're done
              </>
            ) : (
              <>
                <CornerDownLeft size={13} aria-hidden="true" /> to send, Shift +
                Enter for a new line
                {remaining <= 100 ? ` - ${remaining} characters left` : ""}
              </>
            )}
          </span>

          <div className={styles.controls}>
            {micSupported ? (
              <button
                type="button"
                className={`${styles.mic} ${listening ? styles.micLive : ""}`}
                onClick={onMicClick}
                disabled={pending}
                aria-pressed={listening}
                aria-label={listening ? "Stop dictating" : "Ask by voice"}
              >
                {listening ? (
                  <Square size={16} aria-hidden="true" />
                ) : (
                  <Mic size={16} aria-hidden="true" />
                )}
                <span>{listening ? "Stop" : "Speak"}</span>
              </button>
            ) : null}

            <button type="submit" className={styles.send} disabled={!canSend}>
              <Send size={16} aria-hidden="true" />
              <span>Send</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

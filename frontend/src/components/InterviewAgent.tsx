import { useCallback, useEffect, useRef, useState } from "react";

import {
  askInterview,
  fetchAnswerAudio,
  InterviewError,
  type ChatTurn,
} from "../api";
import { CONTACT, INTERVIEW } from "../content";
import {
  ChatPanel,
  type ChatMessage,
  type ChatNoticeState,
} from "../ds/chat";
import { useSpeechRecognition } from "../hooks/useSpeechRecognition";

let nextId = 0;

const GREETING: ChatMessage = {
  id: nextId++,
  role: "agent",
  text: INTERVIEW.greeting,
};

/**
 * Owns the conversation: the API calls, the spoken answers, and dictation.
 * The design system's ChatPanel stays presentational.
 */
export default function InterviewAgent() {
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [notice, setNotice] = useState<ChatNoticeState | null>(null);
  // Session id lives in React state only. Nothing is written to storage.
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [speechAvailable, setSpeechAvailable] = useState(false);
  const [playing, setPlaying] = useState<{ logId: number; loading: boolean } | null>(
    null,
  );

  const abortRef = useRef<AbortController | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioUrlsRef = useRef(new Map<number, string>());
  const audioAbortRef = useRef<AbortController | null>(null);
  // Whatever was typed before dictation started; the transcript is appended to
  // it rather than replacing what the visitor had already written.
  const draftBaseRef = useRef("");

  const onTranscript = useCallback((transcript: string, isFinal: boolean) => {
    const base = draftBaseRef.current;
    setDraft((base ? `${base} ${transcript}` : transcript).slice(0, 500));
    if (isFinal) {
      draftBaseRef.current = "";
    }
  }, []);

  const {
    supported: micSupported,
    listening,
    error: micError,
    start: startListening,
    stop: stopListening,
    setError: setMicError,
  } = useSpeechRecognition({ onTranscript });

  useEffect(() => {
    if (micError) {
      setNotice({ variant: "info", text: micError });
    }
  }, [micError]);

  useEffect(() => {
    const urls = audioUrlsRef.current;
    return () => {
      abortRef.current?.abort();
      audioAbortRef.current?.abort();
      audioRef.current?.pause();
      for (const url of urls.values()) {
        URL.revokeObjectURL(url);
      }
      urls.clear();
    };
  }, []);

  const send = async (question: string) => {
    const trimmed = question.trim();
    if (!trimmed || pending) {
      return;
    }
    if (listening) {
      stopListening();
    }

    const history: ChatTurn[] = messages
      .filter((m) => m.id !== GREETING.id)
      .map((m) => ({ role: m.role === "agent" ? "assistant" : "user", content: m.text }));

    const asked: ChatMessage = { id: nextId++, role: "user", text: trimmed };
    setMessages((current) => [...current, asked]);
    setDraft("");
    draftBaseRef.current = "";
    setNotice(null);
    setMicError(null);
    setPending(true);

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await askInterview(trimmed, history, sessionId, controller.signal);
      setSessionId(result.session_id);
      setSpeechAvailable(result.speech_available);
      setMessages((current) => [
        ...current,
        { id: nextId++, role: "agent", text: result.answer, logId: result.log_id },
      ]);
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      // Take the question back out of the transcript and put it back in the
      // box, so nothing is lost and the thread stays coherent.
      setMessages((current) => current.filter((m) => m.id !== asked.id));
      setDraft(trimmed);

      if (error instanceof InterviewError && error.kind === "throttled") {
        setNotice({
          variant: "limit",
          text: (
            <>
              Rate limit hit — <a href={`mailto:${CONTACT.email}`}>email Cory instead</a>.
              He answers faster than you'd think.
            </>
          ),
        });
      } else {
        setNotice({
          variant: "error",
          text: (
            <>
              {error instanceof InterviewError
                ? error.message
                : "Something went wrong. Try that again."}{" "}
              <a href={`mailto:${CONTACT.email}`}>Or email Cory directly.</a>
            </>
          ),
        });
      }
    } finally {
      setPending(false);
      abortRef.current = null;
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
    setPlaying(null);
  }, []);

  const speak = async (logId: number) => {
    if (playing?.logId === logId) {
      stopPlayback();
      return;
    }
    stopPlayback();
    setNotice(null);
    setPlaying({ logId, loading: true });

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
      setPlaying({ logId, loading: false });
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setPlaying(null);
      setNotice({
        variant: "error",
        text:
          error instanceof InterviewError
            ? error.message
            : "That answer could not be played.",
      });
    }
  };

  return (
    <>
      <audio
        ref={audioRef}
        onEnded={() => setPlaying(null)}
        onError={() => {
          setPlaying(null);
          setNotice({ variant: "error", text: "That answer could not be played." });
        }}
        hidden
      />
      <ChatPanel
        messages={messages}
        draft={draft}
        onDraftChange={setDraft}
        onSend={(text) => void send(text)}
        pending={pending}
        error={notice}
        prompts={messages.length <= 1 ? INTERVIEW.prompts : []}
        note={INTERVIEW.note}
        voice={{
          supported: micSupported,
          listening,
          onToggle: () => {
            if (listening) {
              stopListening();
            } else {
              draftBaseRef.current = draft.trim();
              startListening();
            }
          },
        }}
        listenFor={(m) =>
          speechAvailable && m.role === "agent" && m.logId !== undefined
            ? {
                status:
                  playing?.logId === m.logId
                    ? playing.loading
                      ? "loading"
                      : "playing"
                    : "idle",
                onToggle: () => void speak(m.logId as number),
              }
            : null
        }
      />
    </>
  );
}

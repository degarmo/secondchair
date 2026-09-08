import { useCallback, useEffect, useRef, useState } from "react";

type SpeechRecognitionConstructor = { new (): SpeechRecognition };

function getConstructor(): SpeechRecognitionConstructor | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.SpeechRecognition ?? window.webkitSpeechRecognition ?? null;
}

/** What to tell the visitor when recognition fails. */
function messageFor(code: SpeechRecognitionErrorCode): string | null {
  switch (code) {
    case "not-allowed":
    case "service-not-allowed":
      return "Microphone access is blocked. Allow it in your browser settings, or type instead.";
    case "no-speech":
      return "I didn't catch that. Try again, or type it.";
    case "audio-capture":
      return "No microphone found. Type your question instead.";
    case "network":
      return "Speech recognition needs a connection and couldn't reach it.";
    case "aborted":
      // The visitor stopped it themselves. Not worth a message.
      return null;
    default:
      return "Speech recognition failed. Type your question instead.";
  }
}

interface UseSpeechRecognitionOptions {
  /** Called with the whole utterance so far, replacing any previous value. */
  onTranscript: (transcript: string, isFinal: boolean) => void;
}

/**
 * Dictation via the browser's own speech recognition.
 *
 * Nothing is sent to our server: Chrome and Edge transcribe through Google,
 * Safari through Apple. Firefox has no implementation at all, so `supported`
 * is false there and the caller keeps its textarea.
 */
export function useSpeechRecognition({
  onTranscript,
}: UseSpeechRecognitionOptions) {
  const [supported] = useState(() => getConstructor() !== null);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const callbackRef = useRef(onTranscript);

  useEffect(() => {
    callbackRef.current = onTranscript;
  }, [onTranscript]);

  useEffect(
    () => () => {
      recognitionRef.current?.abort();
      recognitionRef.current = null;
    },
    [],
  );

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
  }, []);

  const start = useCallback(() => {
    const Recognition = getConstructor();
    if (!Recognition || recognitionRef.current) {
      return;
    }

    const recognition = new Recognition();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    // One question at a time: recognition ends on its own when they stop
    // talking, so a forgotten open microphone isn't possible.
    recognition.continuous = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event) => {
      let transcript = "";
      for (let i = 0; i < event.results.length; i += 1) {
        transcript += event.results[i][0].transcript;
      }
      const last = event.results[event.results.length - 1];
      callbackRef.current(transcript.trim(), Boolean(last?.isFinal));
    };

    recognition.onerror = (event) => {
      setError(messageFor(event.error));
    };

    recognition.onend = () => {
      recognitionRef.current = null;
      setListening(false);
    };

    setError(null);
    recognitionRef.current = recognition;

    try {
      recognition.start();
      setListening(true);
    } catch {
      // Safari throws if start() is called while one is already winding down.
      recognitionRef.current = null;
      setListening(false);
    }
  }, []);

  const toggle = useCallback(() => {
    if (listening) {
      stop();
    } else {
      start();
    }
  }, [listening, start, stop]);

  return { supported, listening, error, start, stop, toggle, setError };
}

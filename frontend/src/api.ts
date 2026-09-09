export type ChatRole = "user" | "assistant";

export interface ChatTurn {
  role: ChatRole;
  content: string;
}

export interface InterviewResponse {
  answer: string;
  session_id: string;
  /** Id of the stored answer, used to ask for the spoken version. */
  log_id: number;
  /** False when the site has no voice configured; hide the play button. */
  speech_available: boolean;
}

/** Why an ask failed, in the terms the chat UI needs to react to. */
export type FailureKind = "throttled" | "unavailable" | "invalid" | "network";

export class InterviewError extends Error {
  readonly kind: FailureKind;
  readonly status: number | null;
  /**
   * True when the sentence came from the API rather than from our fallback
   * copy. Server details already say how to get in touch, so the UI does not
   * append a second contact line to them.
   */
  readonly fromServer: boolean;

  constructor(
    kind: FailureKind,
    message: string,
    status: number | null = null,
    fromServer = false,
  ) {
    super(message);
    this.name = "InterviewError";
    this.kind = kind;
    this.status = status;
    this.fromServer = fromServer;
  }
}

/**
 * Render's blueprint can only pass a service's ``host`` — there is no ``url``
 * property — so VITE_API_BASE_URL arrives in production as
 * "cd-site-api.onrender.com" with no scheme. Prefix https:// when one is
 * missing, and leave a full URL (including the http://localhost default)
 * alone.
 */
const API_BASE_URL = (() => {
  const raw = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000")
    .trim()
    .replace(/\/$/, "");
  return /^https?:\/\//.test(raw) ? raw : `https://${raw}`;
})();

async function readDetail(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      if (typeof detail === "string") {
        return detail;
      }
    }
  } catch {
    // Body was not JSON. The caller falls back to its own copy.
  }
  return null;
}

/**
 * What the panel needs on load: whether the site can speak at all. A failure
 * here is not worth surfacing — the panel just leaves the audio switch hidden.
 */
export async function fetchInterviewConfig(
  signal?: AbortSignal,
): Promise<{ speech_available: boolean }> {
  const response = await fetch(`${API_BASE_URL}/api/interview/config/`, { signal });
  if (!response.ok) {
    throw new InterviewError("unavailable", "Config unavailable.", response.status);
  }
  return (await response.json()) as { speech_available: boolean };
}

export async function askInterview(
  question: string,
  history: ChatTurn[],
  sessionId: string | null,
  signal?: AbortSignal,
): Promise<InterviewResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/interview/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        history,
        ...(sessionId ? { session_id: sessionId } : {}),
      }),
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new InterviewError(
      "network",
      "Could not reach the agent. Check your connection and try again.",
    );
  }

  if (!response.ok) {
    const detail = await readDetail(response);

    if (response.status === 429) {
      throw new InterviewError(
        "throttled",
        detail ?? "Too many questions in one hour.",
        429,
        detail !== null,
      );
    }
    if (response.status === 400) {
      throw new InterviewError(
        "invalid",
        detail ?? "That question could not be sent. Keep it under 500 characters.",
        400,
        detail !== null,
      );
    }
    throw new InterviewError(
      "unavailable",
      detail ?? "The agent is having trouble right now.",
      response.status,
      detail !== null,
    );
  }

  return (await response.json()) as InterviewResponse;
}

/**
 * Fetch the spoken version of an answer the agent already gave.
 *
 * Takes an answer id rather than text: the endpoint can only voice
 * sentences the agent itself produced.
 */
export async function fetchAnswerAudio(
  logId: number,
  signal?: AbortSignal,
): Promise<Blob> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/interview/${logId}/speech/`, {
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }
    throw new InterviewError("network", "Could not reach the voice service.");
  }

  if (!response.ok) {
    const detail = await readDetail(response);
    if (response.status === 429) {
      throw new InterviewError(
        "throttled",
        detail ?? "Too many spoken answers in one hour.",
        429,
      );
    }
    throw new InterviewError(
      "unavailable",
      detail ?? "That answer could not be spoken.",
      response.status,
    );
  }

  return await response.blob();
}

import {
  Camera,
  CircleStop,
  Loader2,
  Mic,
  MonitorUp,
  Play,
  Send,
  Video,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8020/api/v1";

function App() {
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState(null);
  const [answerText, setAnswerText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  async function enableMedia() {
    setError("");
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });
      setStream(mediaStream);
      setStatus("Camera and microphone ready");
    } catch {
      setError("Camera and microphone permission is required for the video interview.");
    }
  }

  async function startInterview() {
    setError("");
    setStatus("Creating interview");
    try {
      const response = await fetch(`${API_BASE_URL}/live-interviews/sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_role: "AI Engineer",
          mode: "technical",
          difficulty: "intermediate",
          question_count: 5,
        }),
      });
      if (!response.ok) throw new Error("Could not create interview session");
      const createdSession = await response.json();
      setSession(createdSession);
      setStatus("Interview started");
      await requestNextQuestion(createdSession.session_id);
    } catch (caughtError) {
      setError(caughtError.message);
      setStatus("Ready");
    }
  }

  async function requestNextQuestion(sessionId = session?.session_id) {
    if (!sessionId) return;
    setError("");
    setStatus("Loading question");
    try {
      const response = await fetch(
        `${API_BASE_URL}/live-interviews/sessions/${sessionId}/next-question`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error("Could not load next question");
      const payload = await response.json();
      setQuestion(payload.question);
      setAnswerText("");
      setStatus(payload.question ? "Answering" : "Interview complete");
    } catch (caughtError) {
      setError(caughtError.message);
      setStatus("Ready");
    }
  }

  function toggleRecording() {
    if (!stream) {
      setError("Enable camera and microphone first.");
      return;
    }

    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      setStatus("Recording saved locally");
      return;
    }

    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;
    recorder.start();
    setIsRecording(true);
    setStatus("Recording answer");
  }

  async function submitTranscript() {
    if (!session || !question || !answerText.trim()) return;
    setError("");
    setStatus("Submitting answer");
    try {
      const response = await fetch(
        `${API_BASE_URL}/live-interviews/sessions/${session.session_id}/transcript`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question_id: question.id,
            transcript: answerText,
            duration_seconds: 60,
          }),
        },
      );
      if (!response.ok) throw new Error("Could not submit answer transcript");
      await response.json();
      setStatus("Answer queued for evaluation");
    } catch (caughtError) {
      setError(caughtError.message);
      setStatus("Answering");
    }
  }

  const canStart = Boolean(stream) && !session;

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">Live AI interview</p>
          <h1>AI Interview Copilot</h1>
        </div>
        <span className="status">{status}</span>
      </section>

      <section className="interview-grid">
        <div className="stage">
          <div className="interviewer">
            <MonitorUp aria-hidden="true" />
            <div>
              <p className="label">Interviewer</p>
              <h2>{question?.question_text ?? "Start when you are ready."}</h2>
            </div>
          </div>

          <div className="video-frame">
            {stream ? (
              <video ref={videoRef} autoPlay muted playsInline />
            ) : (
              <div className="camera-empty">
                <Video aria-hidden="true" />
                <span>Camera off</span>
              </div>
            )}
          </div>
        </div>

        <aside className="control-panel">
          <button className="primary" onClick={enableMedia}>
            <Camera size={18} />
            Enable media
          </button>

          <button className="primary" disabled={!canStart} onClick={startInterview}>
            <Play size={18} />
            Start interview
          </button>

          <button className="secondary" disabled={!question} onClick={toggleRecording}>
            {isRecording ? <CircleStop size={18} /> : <Mic size={18} />}
            {isRecording ? "Stop recording" : "Record answer"}
          </button>

          <textarea
            value={answerText}
            onChange={(event) => setAnswerText(event.target.value)}
            placeholder="Transcript appears here after speech-to-text. For this foundation build, paste or type the transcript."
          />

          <button className="secondary" disabled={!answerText.trim()} onClick={submitTranscript}>
            <Send size={18} />
            Submit transcript
          </button>

          <button className="ghost" disabled={!session} onClick={() => requestNextQuestion()}>
            <Loader2 size={18} />
            Next question
          </button>

          {error ? <p className="error">{error}</p> : null}
        </aside>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);


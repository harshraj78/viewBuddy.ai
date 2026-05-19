import {
  BarChart3,
  Bot,
  Camera,
  CheckCircle2,
  CircleStop,
  Code2,
  FileText,
  LayoutTemplate,
  Mic,
  Mic2,
  MonitorUp,
  PenLine,
  Play,
  Send,
  Video,
  Volume2,
} from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8020/api/v1";

const roles = ["SDE", "AI Engineer", "Backend", "Frontend"];
const experiences = ["Fresher", "Mid-level"];
const interviewTypes = ["Technical", "HR", "System Design"];
const companyStyles = ["FAANG", "Startup", "Indian Product"];
const personalities = ["Friendly", "Strict", "FAANG pressure"];

const screenOrder = [
  "landing",
  "setup",
  "waiting",
  "live",
  "coding",
  "system",
  "report",
];

function App() {
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recognitionRef = useRef(null);
  const websocketRef = useRef(null);
  const [screen, setScreen] = useState("landing");
  const [stream, setStream] = useState(null);
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState(null);
  const [answerText, setAnswerText] = useState("");
  const [report, setReport] = useState(null);
  const [reportError, setReportError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcriptOpen, setTranscriptOpen] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const [streamedAiText, setStreamedAiText] = useState("");
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");
  const [setup, setSetup] = useState({
    role: "AI Engineer",
    experience: "Fresher",
    interviewType: "Technical",
    companyStyle: "Indian Product",
    personality: "Friendly",
    resumeName: "",
  });

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream, screen]);

  useEffect(() => {
    if (screen === "live" && question?.question_text) {
      speakQuestion(question.question_text);
    }
  }, [question, screen]);

  useEffect(() => {
    return () => websocketRef.current?.close();
  }, []);

  const stepIndex = screenOrder.indexOf(screen);
  const interviewerTone = useMemo(() => {
    const toneMap = {
      Friendly: "Warm, encouraging, and clear.",
      Strict: "Direct, concise, and detail-oriented.",
      "FAANG pressure": "High bar, fast follow-ups, and tradeoff-focused.",
    };
    return toneMap[setup.personality];
  }, [setup.personality]);

  function updateSetup(field, value) {
    setSetup((current) => ({ ...current, [field]: value }));
  }

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
          target_role: setup.role,
          mode: setup.interviewType.toLowerCase().replace(" ", "_"),
          difficulty: setup.experience === "Fresher" ? "beginner" : "intermediate",
          target_company: setup.companyStyle,
          question_count: 5,
        }),
      });
      if (!response.ok) throw new Error("Could not create interview session");
      const createdSession = await response.json();
      setSession(createdSession);
      connectInterviewSocket(createdSession.session_id);
      setStatus("Interview started");
      await requestNextQuestion(createdSession.session_id);
      setScreen(setup.interviewType === "System Design" ? "system" : "live");
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
      setStreamedAiText("");
      setAnswerText("");
      setStatus(payload.question ? "Answering" : "Interview complete");
      if (!payload.question) setScreen("report");
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
      recognitionRef.current?.stop();
      setIsRecording(false);
      setIsListening(false);
      setStatus("Recording saved locally");
      return;
    }

    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;
    recorder.start();
    startSpeechRecognition();
    setIsRecording(true);
    setStatus("Recording answer");
  }

  function startSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setVoiceMessage("Speech-to-text is not supported in this browser. Type the transcript.");
      setTranscriptOpen(true);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-IN";
    recognition.onstart = () => {
      setIsListening(true);
      setVoiceMessage("Listening...");
      setTranscriptOpen(true);
    };
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0].transcript)
        .join(" ")
        .trim();
      setAnswerText(transcript);
    };
    recognition.onerror = () => {
      setVoiceMessage("Speech recognition paused. You can continue by typing.");
      setIsListening(false);
    };
    recognition.onend = () => {
      setIsListening(false);
      if (isRecording) setVoiceMessage("Speech recognition stopped.");
    };

    recognitionRef.current = recognition;
    recognition.start();
  }

  function speakQuestion(text = question?.question_text) {
    if (!text || !window.speechSynthesis) {
      setVoiceMessage("Text-to-speech is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = setup.personality === "FAANG pressure" ? 1.06 : 0.96;
    utterance.pitch = setup.personality === "Friendly" ? 1.04 : 0.94;
    window.speechSynthesis.speak(utterance);
    setVoiceMessage("Interviewer question is playing.");
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
      sendInterviewEvent("transcript_chunk", {
        question: question.question_text,
        transcript: answerText,
        personality: setup.personality,
      });
      setStatus("Answer queued for evaluation");
      await loadReport();
    } catch (caughtError) {
      setError(caughtError.message);
      setStatus("Answering");
    }
  }

  function connectInterviewSocket(sessionId) {
    websocketRef.current?.close();
    const wsBaseUrl = API_BASE_URL.replace(/^http/, "ws");
    const socket = new WebSocket(`${wsBaseUrl}/live-interviews/sessions/${sessionId}/ws`);
    websocketRef.current = socket;
    socket.onopen = () => setStatus("Realtime interview connected");
    socket.onmessage = (message) => {
      const event = JSON.parse(message.data);
      if (event.type === "ai_response_chunk") {
        setStreamedAiText((current) => `${current} ${event.payload.text}`.trim());
      }
      if (event.type === "followup_question") {
        const followup = event.payload.question;
        setQuestion({
          id: event.payload.question_id,
          order_index: question?.order_index ?? 0,
          question_text: followup,
          question_type: "follow_up",
          expected_answer_seconds: 90,
          preparation_seconds: 5,
        });
        setAnswerText("");
        setStreamedAiText("");
        speakQuestion(followup);
      }
      if (event.type === "state_transition") {
        setStatus(`State: ${event.payload.state}`);
      }
      if (event.type === "error") {
        setError(event.payload.message);
      }
    };
    socket.onclose = () => setVoiceMessage("Realtime connection closed.");
  }

  function sendInterviewEvent(type, payload) {
    if (websocketRef.current?.readyState !== WebSocket.OPEN) {
      setVoiceMessage("Realtime socket is not connected. REST transcript was still saved.");
      return;
    }
    websocketRef.current.send(JSON.stringify({ type, payload }));
  }

  async function loadReport() {
    if (!session) return;
    setReportError("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/live-interviews/sessions/${session.session_id}/report`,
      );
      if (!response.ok) throw new Error("Could not load feedback report");
      setReport(await response.json());
    } catch (caughtError) {
      setReportError(caughtError.message);
    }
  }

  async function enterReport() {
    await loadReport();
    setScreen("report");
  }

  return (
    <main className="app-shell">
      {screen !== "landing" ? (
        <ProgressHeader screen={screen} stepIndex={stepIndex} status={status} />
      ) : null}

      {screen === "landing" ? (
        <LandingScreen onStart={() => setScreen("setup")} />
      ) : null}

      {screen === "setup" ? (
        <SetupScreen
          setup={setup}
          interviewerTone={interviewerTone}
          onChange={updateSetup}
          onNext={() => setScreen("waiting")}
        />
      ) : null}

      {screen === "waiting" ? (
        <WaitingRoom
          stream={stream}
          videoRef={videoRef}
          setup={setup}
          error={error}
          onEnableMedia={enableMedia}
          onStartInterview={startInterview}
        />
      ) : null}

      {screen === "live" ? (
        <LiveInterview
          videoRef={videoRef}
          stream={stream}
          question={question}
          answerText={answerText}
          transcriptOpen={transcriptOpen}
          isRecording={isRecording}
          isListening={isListening}
          voiceMessage={voiceMessage}
          streamedAiText={streamedAiText}
          error={error}
          onToggleTranscript={() => setTranscriptOpen((current) => !current)}
          onAnswerText={setAnswerText}
          onToggleRecording={toggleRecording}
          onSpeakQuestion={() => speakQuestion()}
          onSubmitTranscript={submitTranscript}
          onNextQuestion={() => requestNextQuestion()}
          onCodingRound={() => setScreen("coding")}
          onSystemRound={() => setScreen("system")}
          onLeave={enterReport}
        />
      ) : null}

      {screen === "coding" ? <CodingRound onBack={() => setScreen("live")} /> : null}
      {screen === "system" ? <SystemDesignRound onBack={() => setScreen("live")} /> : null}
      {screen === "report" ? (
        <FeedbackReport
          report={report}
          error={reportError}
          onRestart={() => {
            setSession(null);
            setQuestion(null);
            setReport(null);
            setAnswerText("");
            setScreen("setup");
          }}
        />
      ) : null}
    </main>
  );
}

function ProgressHeader({ screen, stepIndex, status }) {
  return (
    <header className="progress-header">
      <div>
        <p className="eyebrow">viewBuddy.ai</p>
        <h1>{screenLabels[screen]}</h1>
      </div>
      <div className="progress-meta">
        <span>{status}</span>
        <span>
          Step {stepIndex + 1} of {screenOrder.length}
        </span>
      </div>
    </header>
  );
}

const screenLabels = {
  setup: "Interview setup",
  waiting: "Waiting room",
  live: "Live interview",
  coding: "Coding round",
  system: "System design round",
  report: "Feedback report",
};

function LandingScreen({ onStart }) {
  return (
    <section className="landing">
      <nav className="nav">
        <strong>viewBuddy.ai</strong>
        <button className="ghost compact" onClick={onStart}>Start interview</button>
      </nav>

      <section className="hero">
        <div>
          <p className="eyebrow">AI mock interviews for serious candidates</p>
          <h1>Practice like it is a real video interview.</h1>
          <p className="hero-copy">
            Role-specific AI interviews for SDE, AI Engineer, backend, and frontend
            candidates. Built around live conversation, not dashboard noise.
          </p>
          <button className="primary wide" onClick={onStart}>
            <Play size={18} />
            Start interview
          </button>
        </div>
        <div className="demo-preview">
          <div className="mock-video">
            <Bot size={44} />
            <span>AI Interviewer</span>
          </div>
          <div className="mock-question">
            Explain one project where you made an engineering tradeoff.
          </div>
        </div>
      </section>

      <section className="section-band">
        <SectionTitle title="Interview types" />
        <div className="three-grid">
          <InfoCard icon={<Mic2 />} title="Technical" text="Project deep dives, fundamentals, and production thinking." />
          <InfoCard icon={<Code2 />} title="Coding" text="LeetCode-style rounds with hints and optimization probes." />
          <InfoCard icon={<LayoutTemplate />} title="System design" text="Architecture prompts with a focused whiteboard mode." />
        </div>
      </section>

      <section className="section-band">
        <SectionTitle title="What candidates say" />
        <div className="three-grid">
          <Quote text="The waiting room made it feel like an actual interview, not another chatbot." />
          <Quote text="Follow-up questions forced me to explain tradeoffs clearly." />
          <Quote text="The report separated communication gaps from technical gaps." />
        </div>
      </section>

      <section className="cta-strip">
        <h2>Ready for your next mock interview?</h2>
        <button className="primary" onClick={onStart}>
          <Video size={18} />
          Enter setup
        </button>
      </section>
    </section>
  );
}

function SetupScreen({ setup, interviewerTone, onChange, onNext }) {
  return (
    <section className="setup-grid">
      <div className="panel">
        <SectionTitle title="Configure interview" />
        <SelectGroup label="Role" value={setup.role} options={roles} onChange={(value) => onChange("role", value)} />
        <SelectGroup label="Experience" value={setup.experience} options={experiences} onChange={(value) => onChange("experience", value)} />
        <SelectGroup label="Interview type" value={setup.interviewType} options={interviewTypes} onChange={(value) => onChange("interviewType", value)} />
        <SelectGroup label="Company style" value={setup.companyStyle} options={companyStyles} onChange={(value) => onChange("companyStyle", value)} />
        <SelectGroup label="Personality" value={setup.personality} options={personalities} onChange={(value) => onChange("personality", value)} />
        <label className="upload-box">
          <FileText size={18} />
          <span>{setup.resumeName || "Upload resume PDF or DOCX"}</span>
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(event) => onChange("resumeName", event.target.files?.[0]?.name ?? "")}
          />
        </label>
        <button className="primary wide" onClick={onNext}>
          Continue to waiting room
        </button>
      </div>

      <div className="panel preview-panel">
        <SectionTitle title="Interviewer preview" />
        <div className="interviewer-avatar">
          <Bot size={48} />
        </div>
        <h2>{setup.personality} interviewer</h2>
        <p>{interviewerTone}</p>
        <div className="preview-line">
          <span>Role</span>
          <strong>{setup.role}</strong>
        </div>
        <div className="preview-line">
          <span>Style</span>
          <strong>{setup.companyStyle}</strong>
        </div>
        <div className="preview-line">
          <span>Round</span>
          <strong>{setup.interviewType}</strong>
        </div>
      </div>
    </section>
  );
}

function WaitingRoom({ stream, videoRef, setup, error, onEnableMedia, onStartInterview }) {
  return (
    <section className="waiting-grid">
      <div className="panel">
        <SectionTitle title="Camera test" />
        <VideoTile stream={stream} videoRef={videoRef} />
        {error ? <p className="error">{error}</p> : null}
        <div className="button-row">
          <button className="secondary" onClick={onEnableMedia}>
            <Camera size={18} />
            Test camera
          </button>
          <button className="secondary" onClick={onEnableMedia}>
            <Mic size={18} />
            Test mic
          </button>
        </div>
      </div>

      <div className="panel">
        <SectionTitle title="AI interviewer intro" />
        <div className="intro-card">
          <Volume2 size={24} />
          <p>
            I will run a {setup.companyStyle} style {setup.interviewType.toLowerCase()} round
            for a {setup.role} role. Keep answers structured and speak naturally.
          </p>
        </div>
        <ul className="tips">
          <li>Look at the camera when explaining decisions.</li>
          <li>Use examples, tradeoffs, and measurable outcomes.</li>
          <li>Ask for clarification if the question is ambiguous.</li>
        </ul>
        <button className="primary wide" disabled={!stream} onClick={onStartInterview}>
          <Play size={18} />
          Start live interview
        </button>
      </div>
    </section>
  );
}

function LiveInterview({
  videoRef,
  stream,
  question,
  answerText,
  transcriptOpen,
  isRecording,
  isListening,
  voiceMessage,
  streamedAiText,
  error,
  onToggleTranscript,
  onAnswerText,
  onToggleRecording,
  onSpeakQuestion,
  onSubmitTranscript,
  onNextQuestion,
  onCodingRound,
  onSystemRound,
  onLeave,
}) {
  return (
    <section className="live-shell">
      <div className="ai-video">
        <Bot size={56} />
        <span>AI Interviewer</span>
      </div>

      <div className="question-card">
        <p className="label">Current question</p>
        <h2>{question?.question_text ?? "Interview complete. You can leave for feedback."}</h2>
        {streamedAiText ? <p className="streamed-ai">{streamedAiText}</p> : null}
        <div className="question-actions">
          <button className="ghost compact" onClick={onSpeakQuestion}>
            <Volume2 size={16} />
            Repeat question
          </button>
          {voiceMessage ? <span>{voiceMessage}</span> : null}
        </div>
      </div>

      <details className="transcript" open={transcriptOpen} onToggle={onToggleTranscript}>
        <summary>Live transcript</summary>
        <textarea
          value={answerText}
          onChange={(event) => onAnswerText(event.target.value)}
          placeholder="Speech-to-text will appear here. For now, type or paste the transcript."
        />
      </details>

      <div className="candidate-pill">
        <VideoTile stream={stream} videoRef={videoRef} compact />
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="live-controls">
        <button className="secondary icon-button" onClick={onToggleRecording}>
          {isRecording ? <CircleStop size={18} /> : <Mic size={18} />}
          {isListening ? "Listening" : isRecording ? "Stop" : "Mic"}
        </button>
        <button className="secondary icon-button">
          <Camera size={18} />
          Cam
        </button>
        <button className="secondary icon-button" onClick={onSubmitTranscript}>
          <Send size={18} />
          Submit
        </button>
        <button className="secondary icon-button" onClick={onNextQuestion}>
          <Play size={18} />
          Next
        </button>
        <button className="ghost icon-button" onClick={onCodingRound}>
          <Code2 size={18} />
          Code
        </button>
        <button className="ghost icon-button" onClick={onSystemRound}>
          <LayoutTemplate size={18} />
          Design
        </button>
        <button className="danger icon-button" onClick={onLeave}>
          Leave
        </button>
        <button className="ghost icon-button">
          <PenLine size={18} />
          Notes
        </button>
      </div>
    </section>
  );
}

function CodingRound({ onBack }) {
  return (
    <section className="coding-layout">
      <div className="problem-panel">
        <SectionTitle title="Problem description" />
        <h2>Design a rate limiter</h2>
        <p>
          Implement a function that decides whether a user request should be allowed
          based on a maximum number of requests per minute.
        </p>
        <ul className="tips">
          <li>Discuss data structures first.</li>
          <li>Explain time and space complexity.</li>
          <li>Optimize after getting a working approach.</li>
        </ul>
      </div>
      <div className="coding-interviewer">
        <Bot size={32} />
        <p>I will observe pauses and ask hints only when needed.</p>
      </div>
      <div className="editor-panel">
        <pre>{`function allowRequest(userId, timestamp) {\n  // Monaco editor will mount here.\n}`}</pre>
      </div>
      <button className="ghost compact" onClick={onBack}>Back to interview</button>
    </section>
  );
}

function SystemDesignRound({ onBack }) {
  return (
    <section className="system-layout">
      <div className="question-card">
        <p className="label">AI interviewer question</p>
        <h2>Design a resume-aware AI mock interview platform for 10,000 daily users.</h2>
      </div>
      <div className="whiteboard">
        <span>Whiteboard / architecture canvas</span>
      </div>
      <button className="ghost compact" onClick={onBack}>Back to interview</button>
    </section>
  );
}

function FeedbackReport({ report, error, onRestart }) {
  const communicationItems = report
    ? [
        `Score: ${report.communication.score}/100`,
        ...report.communication.strengths,
        ...report.communication.improvements,
      ]
    : ["Submit at least one answer transcript to generate communication feedback."];
  const technicalItems = report
    ? [
        `Score: ${report.technical.score}/100`,
        ...report.technical.strengths,
        ...report.technical.improvements,
      ]
    : ["Technical feedback will appear after transcript evaluation."];
  const behavioralItems = report
    ? [
        `Score: ${report.behavioral.score}/100`,
        ...report.behavioral.strengths,
        ...report.behavioral.improvements,
      ]
    : ["Behavioral feedback will appear after transcript evaluation."];
  const replayItems = report?.replay?.length
    ? report.replay.map((item) => `${item.question_text} — ${item.transcript}`)
    : ["Recording placeholder", "Transcript replay appears after answer submission."];

  return (
    <section className="report">
      <div className="report-hero">
        <CheckCircle2 size={36} />
        <div>
          <p className="eyebrow">Interview complete</p>
          <h2>
            {report
              ? `Overall score: ${report.overall_score}/100`
              : "Feedback belongs here, after the pressure is over."}
          </h2>
          {report ? (
            <p>
              Evaluator: {report.evaluator} · Prompt: {report.prompt_version}
            </p>
          ) : null}
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="report-grid">
        <ReportCard title="Communication" items={communicationItems} />
        <ReportCard title="Technical" items={technicalItems} />
        <ReportCard title="Behavioral" items={behavioralItems} />
        <ReportCard title="Replay" items={replayItems} />
      </div>

      <div className="improvement">
        <BarChart3 size={24} />
        <div>
          <h3>Improvement suggestions</h3>
          {(report?.improvement_suggestions ?? [
            "Complete one live answer to generate personalized suggestions.",
          ]).map((item) => (
            <p key={item}>{item}</p>
          ))}
        </div>
      </div>
      <button className="primary" onClick={onRestart}>Start another interview</button>
    </section>
  );
}

function VideoTile({ stream, videoRef, compact = false }) {
  return (
    <div className={compact ? "video-tile compact-video" : "video-tile"}>
      {stream ? (
        <video ref={videoRef} autoPlay muted playsInline />
      ) : (
        <div className="camera-empty">
          <Video aria-hidden="true" />
          <span>Camera off</span>
        </div>
      )}
    </div>
  );
}

function SelectGroup({ label, value, options, onChange }) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
    </label>
  );
}

function SectionTitle({ title }) {
  return <h2 className="section-title">{title}</h2>;
}

function InfoCard({ icon, title, text }) {
  return (
    <article className="info-card">
      {icon}
      <h3>{title}</h3>
      <p>{text}</p>
    </article>
  );
}

function Quote({ text }) {
  return (
    <blockquote className="quote">
      <p>{text}</p>
    </blockquote>
  );
}

function ReportCard({ title, items }) {
  return (
    <article className="report-card">
      <h3>{title}</h3>
      {items.map((item) => (
        <p key={item}>{item}</p>
      ))}
    </article>
  );
}

createRoot(document.getElementById("root")).render(<App />);

import {
  BarChart3,
  Bot,
  Camera,
  CameraOff,
  ChevronDown,
  CheckCircle2,
  CircleStop,
  Clock3,
  Code2,
  FileText,
  Headphones,
  Hand,
  LayoutTemplate,
  Mic,
  Mic2,
  Moon,
  Play,
  Send,
  Share2,
  Sparkles,
  Sun,
  Video,
  Volume2,
} from "lucide-react";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8020/api/v1";

const roles = ["SDE", "AI Engineer", "Backend", "Frontend"];
const experiences = ["Entry Level", "Fresher", "Mid-level"];
const interviewTypes = ["Full Interview (45 mins)", "Technical", "HR", "System Design"];
const companyStyles = ["FAANG", "Startup", "Indian Product"];
const interviewers = ["Basic Interviewer", "Senior Engineer", "FAANG Bar Raiser"];
const personalities = ["Easy Going", "Friendly", "Strict", "FAANG pressure"];
const accents = ["US American", "Indian English", "British English"];
const codingLanguages = ["Python", "JavaScript", "Java", "C++"];
const liveStages = ["Intro", "Clarify", "Discuss", "Coding", "Testing", "Complexity", "Outro"];

const screenOrder = [
  "landing",
  "setup",
  "waiting",
  "live",
  "coding",
  "system",
  "report",
];

function createClientId(prefix = "client") {
  return `${prefix}-${globalThis.crypto?.randomUUID?.() ?? Date.now()}`;
}

function App() {
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const recognitionRef = useRef(null);
  const websocketRef = useRef(null);
  const questionRef = useRef(null);
  const setupRef = useRef(null);
  const sessionRef = useRef(null);
  const answerTextRef = useRef("");
  const isRecordingRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const isSubmittingTranscriptRef = useRef(false);
  const transcriptStartedAtRef = useRef(null);
  const lastTranscriptDeltaAtRef = useRef(0);
  const processedSocketMessagesRef = useRef(new Set());
  const [screen, setScreen] = useState("landing");
  const [stream, setStream] = useState(null);
  const [session, setSession] = useState(null);
  const [question, setQuestion] = useState(null);
  const [answerText, setAnswerText] = useState("");
  const [conversationMessages, setConversationMessages] = useState([]);
  const [report, setReport] = useState(null);
  const [reportError, setReportError] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcriptOpen, setTranscriptOpen] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState("");
  const [streamedAiText, setStreamedAiText] = useState("");
  const [status, setStatus] = useState("Ready");
  const [error, setError] = useState("");
  const [theme, setTheme] = useState(
    () => localStorage.getItem("viewbuddy-theme") || "dark",
  );
  const [setup, setSetup] = useState({
    role: "AI Engineer",
    experience: "Entry Level",
    interviewType: "Full Interview (45 mins)",
    companyStyle: "Indian Product",
    interviewer: "Basic Interviewer",
    personality: "Easy Going",
    accent: "US American",
    candidateName: "Harsh Raj",
    language: "Python",
    resumeName: "",
    resumeContext: "",
  });

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream, screen]);

  useEffect(() => {
    questionRef.current = question;
  }, [question]);

  useEffect(() => {
    setupRef.current = setup;
  }, [setup]);

  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  useEffect(() => {
    isSpeakingRef.current = isSpeaking;
  }, [isSpeaking]);

  useEffect(() => {
    answerTextRef.current = answerText;
  }, [answerText]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("viewbuddy-theme", theme);
  }, [theme]);

  useEffect(() => {
    return () => {
      window.speechSynthesis?.cancel();
      recognitionRef.current?.stop();
      websocketRef.current?.close();
    };
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

  async function updateResumeFile(file) {
    if (!file) {
      setSetup((current) => ({ ...current, resumeName: "", resumeContext: "" }));
      return;
    }

    let resumeContext = `Resume file uploaded: ${file.name}.`;
    if (file.type.startsWith("text/") || /\.(txt|md)$/i.test(file.name)) {
      resumeContext = (await file.text()).slice(0, 10000);
    }

    setSetup((current) => ({
      ...current,
      resumeName: file.name,
      resumeContext,
    }));
  }

  function updateAnswerText(value) {
    answerTextRef.current = value;
    setAnswerText(value);
  }

  function appendConversationMessage(message) {
    setConversationMessages((current) => {
      if (current.some((item) => item.id === message.id)) return current;
      return [
        ...current,
        {
          id: message.id ?? createClientId("message"),
          speaker: message.speaker,
          text: message.text,
          isStreaming: Boolean(message.isStreaming),
        },
      ];
    });
  }

  function appendStreamingMessage(messageId, speaker, chunk) {
    if (!chunk) return;
    setConversationMessages((current) => {
      const existing = current.find((item) => item.id === messageId);
      if (!existing) {
        return [
          ...current,
          {
            id: messageId,
            speaker,
            text: chunk,
            isStreaming: true,
          },
        ];
      }

      return current.map((item) =>
        item.id === messageId
          ? { ...item, text: `${item.text} ${chunk}`.trim(), isStreaming: true }
          : item,
      );
    });
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
          candidate_name: setup.candidateName,
          mode: normalizeInterviewMode(setup.interviewType),
          difficulty: setup.experience === "Entry Level" || setup.experience === "Fresher" ? "beginner" : "intermediate",
          target_company: setup.companyStyle,
          interviewer_name: selectedInterviewerName(setup),
          interviewer_persona: `${setup.interviewer} - ${setup.personality}`,
          interviewer_accent: setup.accent,
          interview_duration_minutes: setup.interviewType.includes("45") ? 45 : 30,
          candidate_skills: [],
          project_highlights: [],
          resume_summary: buildResumeContext(setup),
          question_count: 5,
        }),
      });
      if (!response.ok) throw new Error("Could not create interview session");
      const createdSession = await response.json();
      setSession(createdSession);
      setStatus("Interview started");
      await requestNextQuestion(createdSession.session_id);
      connectInterviewSocket(createdSession.session_id);
      setScreen(normalizeInterviewMode(setup.interviewType) === "system_design" ? "system" : "live");
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
      updateAnswerText("");
      if (payload.question?.question_text) {
        appendConversationMessage({
          id: payload.question.id,
          speaker: "interviewer",
          text: payload.question.question_text,
        });
        speakQuestion(payload.question.question_text);
      }
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
      isRecordingRef.current = false;
      mediaRecorderRef.current?.stop();
      recognitionRef.current?.stop();
      recognitionRef.current = null;
      setIsRecording(false);
      setIsListening(false);
      setStatus("Processing answer");
      submitTranscript(answerTextRef.current);
      return;
    }

    if (isSpeakingRef.current) {
      window.speechSynthesis?.cancel();
      isSpeakingRef.current = false;
      setIsSpeaking(false);
    }

    const recorder = new MediaRecorder(stream);
    mediaRecorderRef.current = recorder;
    recorder.start();
    transcriptStartedAtRef.current = Date.now();
    isRecordingRef.current = true;
    startSpeechRecognition();
    setIsRecording(true);
    setStatus("Recording answer");
  }

  function startSpeechRecognition() {
    if (recognitionRef.current) return;

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
      let finalTranscript = "";
      let interimTranscript = "";
      for (let index = 0; index < event.results.length; index += 1) {
        const result = event.results[index];
        if (result.isFinal) {
          finalTranscript += `${result[0].transcript} `;
        } else {
          interimTranscript += `${result[0].transcript} `;
        }
      }
      const transcript = `${finalTranscript}${interimTranscript}`.trim();
      updateAnswerText(transcript);
      sendLiveTranscriptDelta(transcript);
    };
    recognition.onerror = () => {
      setVoiceMessage("Speech recognition paused. You can continue by typing.");
      setIsListening(false);
    };
    recognition.onend = () => {
      setIsListening(false);
      recognitionRef.current = null;
      if (isRecordingRef.current && !isSpeakingRef.current) {
        setVoiceMessage("Speech recognition restarted.");
        window.setTimeout(() => {
          if (isRecordingRef.current && !isSpeakingRef.current && !recognitionRef.current) {
            startSpeechRecognition();
          }
        }, 400);
      }
    };

    recognitionRef.current = recognition;
    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
      setVoiceMessage("Speech recognition is already starting. Try again in a moment.");
    }
  }

  function speakQuestion(text = questionRef.current?.question_text) {
    if (!text || !window.speechSynthesis) {
      setVoiceMessage("Text-to-speech is not supported in this browser.");
      return;
    }

    recognitionRef.current?.stop();
    isSpeakingRef.current = true;
    setIsSpeaking(true);
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "en-IN";
    utterance.rate = setupRef.current?.personality === "FAANG pressure" ? 1.06 : 0.96;
    utterance.pitch = setupRef.current?.personality === "Easy Going" ? 1.04 : 0.94;
    utterance.onstart = () => {
      setIsSpeaking(true);
      setVoiceMessage("Interviewer is speaking.");
    };
    utterance.onend = () => {
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      setVoiceMessage("Your turn to answer.");
      if (isRecordingRef.current && !recognitionRef.current) {
        window.setTimeout(() => {
          if (isRecordingRef.current && !isSpeakingRef.current && !recognitionRef.current) {
            startSpeechRecognition();
          }
        }, 250);
      }
    };
    utterance.onerror = () => {
      isSpeakingRef.current = false;
      setIsSpeaking(false);
      setVoiceMessage("Voice playback stopped.");
      if (isRecordingRef.current && !recognitionRef.current) {
        startSpeechRecognition();
      }
    };
    window.speechSynthesis.speak(utterance);
  }

  function sendLiveTranscriptDelta(transcript) {
    const activeQuestion = questionRef.current;
    if (!activeQuestion || !transcript) return;

    const now = Date.now();
    if (now - lastTranscriptDeltaAtRef.current < 700) return;
    lastTranscriptDeltaAtRef.current = now;

    sendInterviewEvent(
      "transcript_delta",
      {
        question_id: activeQuestion.id,
        question: activeQuestion.question_text,
        transcript,
        personality: setupRef.current?.personality,
      },
      createClientId("delta"),
      { silentWhenClosed: true },
    );
  }

  async function submitTranscript(transcriptOverride = answerTextRef.current) {
    const activeSession = sessionRef.current;
    const activeQuestion = questionRef.current;
    const transcript =
      typeof transcriptOverride === "string"
        ? transcriptOverride.trim()
        : answerTextRef.current.trim();
    if (!activeSession || !activeQuestion || !transcript) return;
    if (isSubmittingTranscriptRef.current) return;
    isSubmittingTranscriptRef.current = true;
    setError("");
    setStatus("Submitting answer");
    const clientEventId = createClientId("transcript");
    const durationSeconds = transcriptStartedAtRef.current
      ? Math.max(1, Math.round((Date.now() - transcriptStartedAtRef.current) / 1000))
      : 60;
    try {
      const response = await fetch(
        `${API_BASE_URL}/live-interviews/sessions/${activeSession.session_id}/transcript`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question_id: activeQuestion.id,
            transcript,
            duration_seconds: durationSeconds,
          }),
        },
      );
      if (!response.ok) throw new Error("Could not submit answer transcript");
      await response.json();
      appendConversationMessage({
        id: clientEventId,
        speaker: "candidate",
        text: transcript,
      });
      sendInterviewEvent(
        "transcript_final",
        {
          question_id: activeQuestion.id,
          question: activeQuestion.question_text,
          transcript,
          personality: setupRef.current?.personality,
        },
        clientEventId,
      );
      updateAnswerText("");
      transcriptStartedAtRef.current = null;
      setStatus("Answer queued for evaluation");
      await loadReport();
    } catch (caughtError) {
      setError(caughtError.message);
      setStatus("Answering");
    } finally {
      isSubmittingTranscriptRef.current = false;
    }
  }

  function connectInterviewSocket(sessionId) {
    websocketRef.current?.close();
    processedSocketMessagesRef.current = new Set();
    const wsBaseUrl = API_BASE_URL.replace(/^http/, "ws");
    const socket = new WebSocket(`${wsBaseUrl}/live-interviews/sessions/${sessionId}/ws`);
    websocketRef.current = socket;
    socket.onopen = () => setStatus("Realtime interview connected");
    socket.onmessage = (message) => {
      const event = JSON.parse(message.data);
      const messageId = event.event_id ?? event.payload?.message_id;
      if (messageId && processedSocketMessagesRef.current.has(`${event.type}:${messageId}:${event.payload?.text ?? ""}`)) {
        return;
      }
      if (messageId) {
        processedSocketMessagesRef.current.add(`${event.type}:${messageId}:${event.payload?.text ?? ""}`);
      }

      if (event.type === "ai_response_chunk") {
        const text = event.payload.text ?? "";
        if (!text) return;
        setStreamedAiText((current) => `${current} ${text}`.trim());
        if (event.payload.message_id) {
          appendStreamingMessage(
            event.payload.message_id,
            event.payload.speaker ?? "interviewer",
            text,
          );
        }
      }
      if (event.type === "followup_question") {
        const followup = event.payload.question;
        setQuestion({
          id: event.payload.question_id,
          order_index: questionRef.current?.order_index ?? 0,
          question_text: followup,
          question_type: "follow_up",
          expected_answer_seconds: 90,
          preparation_seconds: 5,
        });
        updateAnswerText("");
        setStreamedAiText("");
        speakQuestion(followup);
      }
      if (event.type === "interviewer_interrupt") {
        const text = event.payload.text ?? "";
        if (!text) return;
        appendConversationMessage({
          id: event.payload.message_id ?? createClientId("interrupt"),
          speaker: "interviewer",
          text,
        });
        setVoiceMessage("Interviewer redirected your answer.");
        speakQuestion(text);
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

  function sendInterviewEvent(
    type,
    payload,
    eventId = createClientId(type),
    options = {},
  ) {
    if (websocketRef.current?.readyState !== WebSocket.OPEN) {
      if (!options.silentWhenClosed) {
        setVoiceMessage("Realtime socket is not connected. REST transcript was still saved.");
      }
      return;
    }
    websocketRef.current.send(JSON.stringify({ type, payload, event_id: eventId }));
  }

  async function loadReport() {
    const activeSession = sessionRef.current;
    if (!activeSession) return;
    setReportError("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/live-interviews/sessions/${activeSession.session_id}/report`,
      );
      if (!response.ok) throw new Error("Could not load feedback report");
      setReport(await response.json());
    } catch (caughtError) {
      setReportError(caughtError.message);
    }
  }

  async function enterReport() {
    sendInterviewEvent("interview_complete", { reason: "candidate_left" });
    websocketRef.current?.close();
    recognitionRef.current?.stop();
    window.speechSynthesis?.cancel();
    isRecordingRef.current = false;
    isSpeakingRef.current = false;
    setIsRecording(false);
    setIsListening(false);
    setIsSpeaking(false);
    await loadReport();
    setScreen("report");
  }

  return (
    <main className="app-shell">
      {screen !== "landing" ? (
        <ProgressHeader
          screen={screen}
          stepIndex={stepIndex}
          status={status}
          theme={theme}
          onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
        />
      ) : null}

      {screen === "landing" ? (
        <LandingScreen
          onStart={() => setScreen("setup")}
          theme={theme}
          onToggleTheme={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
        />
      ) : null}

      {screen === "setup" ? (
        <SetupScreen
          setup={setup}
          interviewerTone={interviewerTone}
          onChange={updateSetup}
          onResumeFile={updateResumeFile}
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
          setup={setup}
          answerText={answerText}
          transcriptOpen={transcriptOpen}
          isRecording={isRecording}
          isListening={isListening}
          isSpeaking={isSpeaking}
          voiceMessage={voiceMessage}
          streamedAiText={streamedAiText}
          conversationMessages={conversationMessages}
          error={error}
          onToggleTranscript={() => setTranscriptOpen((current) => !current)}
          onAnswerText={updateAnswerText}
          onToggleRecording={toggleRecording}
          onSpeakQuestion={() => speakQuestion()}
          onSubmitTranscript={submitTranscript}
          onNextQuestion={() => requestNextQuestion()}
          onCodingRound={() => setScreen("coding")}
          onSystemRound={() => setScreen("system")}
          onLeave={enterReport}
          onInterrupt={() => {
            window.speechSynthesis?.cancel();
            if (!isRecordingRef.current) toggleRecording();
          }}
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
            updateAnswerText("");
            setConversationMessages([]);
            setStreamedAiText("");
            setScreen("setup");
          }}
        />
      ) : null}
    </main>
  );
}

function normalizeInterviewMode(value) {
  if (value === "Full Interview (45 mins)") return "technical";
  return value.toLowerCase().replace(" ", "_");
}

function selectedInterviewerName(setup) {
  if (setup.interviewer === "FAANG Bar Raiser") return "Sarah";
  if (setup.interviewer === "Senior Engineer") return "Alex";
  return "Sarah";
}

function buildResumeContext(setup) {
  if (!setup.resumeName && !setup.resumeContext) return null;
  return [
    setup.resumeContext || `Resume file uploaded: ${setup.resumeName}.`,
    `Interview target: ${setup.role}, ${setup.companyStyle}, ${setup.experience}.`,
    "Use this resume context as the primary memory source for resume-based questions.",
  ].join("\n");
}

function ThemeToggle({ theme, onToggleTheme }) {
  return (
    <button className="theme-toggle" onClick={onToggleTheme} aria-label="Toggle theme">
      {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

function ProgressHeader({ screen, stepIndex, status, theme, onToggleTheme }) {
  return (
    <header className="progress-header">
      <div>
        <p className="eyebrow">viewBuddy.ai</p>
        <h1>{screenLabels[screen]}</h1>
      </div>
      <div className="progress-meta">
        <ThemeToggle theme={theme} onToggleTheme={onToggleTheme} />
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

function LandingScreen({ onStart, theme, onToggleTheme }) {
  return (
    <section className="landing">
      <nav className="nav">
        <strong>viewBuddy.ai</strong>
        <div className="nav-actions">
          <ThemeToggle theme={theme} onToggleTheme={onToggleTheme} />
          <button className="ghost compact" onClick={onStart}>Start interview</button>
        </div>
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

function SetupScreen({ setup, interviewerTone, onChange, onResumeFile, onNext }) {
  return (
    <section className="customize-shell">
      <div className="customize-card">
        <h1>Customize Your Mock Interview</h1>
        <p className="muted-copy">
          You can customize the personality and the accent of the interviewer.
        </p>
        <SelectGroup label="Interviewer" value={setup.interviewer} options={interviewers} onChange={(value) => onChange("interviewer", value)} />
        <SelectGroup label="Interview Mode" value={setup.interviewType} options={interviewTypes} onChange={(value) => onChange("interviewType", value)} badge="New" />
        <SelectGroup label="Difficulty" value={setup.experience} options={experiences} onChange={(value) => onChange("experience", value)} />
        <SelectGroup label="Personality" value={setup.personality} options={personalities} onChange={(value) => onChange("personality", value)} />
        <SelectGroup label="Accent" value={setup.accent} options={accents} onChange={(value) => onChange("accent", value)} emphasized />
        <SelectGroup label="Role" value={setup.role} options={roles} onChange={(value) => onChange("role", value)} />
        <SelectGroup label="Company style" value={setup.companyStyle} options={companyStyles} onChange={(value) => onChange("companyStyle", value)} />
        <TextInputGroup label="Candidate name" value={setup.candidateName} onChange={(value) => onChange("candidateName", value)} />
        <label className={setup.resumeName ? "upload-box has-file" : "upload-box"}>
          <FileText size={18} />
          <span>{setup.resumeName || "Upload resume"}</span>
          <input
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={(event) => onResumeFile(event.target.files?.[0])}
          />
        </label>
        <div className="premium-note">
          <Sparkles size={17} />
          <span>Premium roadmap: deeper resume memory, longer interviews, coding observation, and company-specific rounds.</span>
        </div>
        <div className="setup-footer-note">
          <Headphones size={18} />
          <span>This interview will take 45 minutes. Put on headphones for better sound quality.</span>
        </div>
        <div className="setup-actions">
          <button className="ghost" onClick={() => onResumeFile(null)}>Clear resume</button>
          <button className="primary" onClick={onNext}>
            Start Interview
            <Headphones size={17} />
          </button>
        </div>
        <p className="setup-tone">{interviewerTone}</p>
      </div>
    </section>
  );
}

function WaitingRoom({ stream, videoRef, setup, error, onEnableMedia, onStartInterview }) {
  return (
    <section className="mock-waiting">
      <BrandBar />
      <div className="waiting-stage">
        <div className="candidate-preview">
          <VideoTile stream={stream} videoRef={videoRef} />
          <div className="avatar-fallback">{setup.candidateName?.[0] ?? "C"}</div>
          <div className="waiting-controls">
            <button className="round-danger" onClick={onEnableMedia}><Mic size={18} /></button>
            <button className="round-danger" onClick={onEnableMedia}><CameraOff size={18} /></button>
          </div>
          <span className="candidate-label">{setup.candidateName}</span>
        </div>
      </div>

      <div className="waiting-form">
        <h1>Welcome to the Interview</h1>
        <TextInputGroup label="Name" value={setup.candidateName} onChange={() => {}} readonly />
        <SelectGroup label="Choose Language" value={setup.language} options={codingLanguages} onChange={() => {}} />
        <div className="media-heading">Media Settings</div>
        <button className="device-select" onClick={onEnableMedia}>
          <Mic size={18} />
          Audio Input
          <ChevronDown size={18} />
        </button>
        <p className="muted-copy small">
          Please enable audio access, select a functional audio device, and test it thoroughly before the interview starts.
        </p>
        <button className="device-select">
          <Share2 size={18} />
          Share your screen (optional)
        </button>
        <p className="muted-copy small">
          Optional: share your screen to let ViewBuddy observe your coding process.
        </p>
        {error ? <p className="error">{error}</p> : null}
        <button className="primary waiting-continue" disabled={!stream} onClick={onStartInterview}>
          Continue
        </button>
        {!stream ? (
          <button className="ghost waiting-continue" onClick={onEnableMedia}>
            Enable camera and mic
          </button>
        ) : null}
      </div>
    </section>
  );
}

function BrandBar() {
  return (
    <nav className="mock-brand">
      <div>
        <Sparkles size={22} />
        <strong>ViewBuddy</strong>
      </div>
    </nav>
  );
}

function PhaseRail({ active = "Intro" }) {
  return (
    <div className="phase-rail">
      {liveStages.map((stage) => (
        <span className={stage === active ? "phase active" : "phase"} key={stage}>
          {stage === "Intro" ? "done" : "dot"} {stage}
        </span>
      ))}
    </div>
  );
}

function LiveInterview({
  videoRef,
  stream,
  setup,
  question,
  answerText,
  transcriptOpen,
  isRecording,
  isListening,
  isSpeaking,
  voiceMessage,
  streamedAiText,
  conversationMessages,
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
  onInterrupt,
}) {
  return (
    <section className="mock-live">
      <BrandBar />
      <div className="live-topbar">
        <PhaseRail active={question?.question_type === "follow_up" ? "Clarify" : "Intro"} />
        <div className="timer-pill"><Clock3 size={18} />44:39</div>
      </div>

      <div className="interview-grid">
        <div className="participant candidate">
          <h2>{setup.candidateName}</h2>
          <div className="participant-video">
            <VideoTile stream={stream} videoRef={videoRef} compact />
            <div className="participant-footer">
              <span>{setup.candidateName}</span>
              <button className="round-danger" onClick={onToggleRecording}>
                {isRecording ? <CircleStop size={18} /> : <Mic size={18} />}
              </button>
              <button className="round-ghost"><Camera size={18} /></button>
            </div>
          </div>
        </div>

        <div className="participant interviewer">
          <h2>{selectedInterviewerName(setup)}</h2>
          <div className="participant-video interviewer-panel">
            <div className="interviewer-photo">{selectedInterviewerName(setup)[0]}</div>
            {isSpeaking ? <span className="speaking-indicator"><Volume2 size={18} /></span> : null}
            <button className="interrupt-button" onClick={onInterrupt}>
              <Hand size={20} />
              Click to Interrupt
            </button>
            <button className="round-light"><CameraOff size={20} /></button>
          </div>
        </div>
      </div>

      <div className="live-caption">
        {conversationMessages.slice(-3).map((message) => (
          <p key={message.id}>
            <strong>{message.speaker === "candidate" ? setup.candidateName : "AI"}:</strong> {message.text}
          </p>
        ))}
        {streamedAiText ? <p><strong>AI:</strong> {streamedAiText}</p> : null}
        {answerText ? <p><strong>{setup.candidateName}:</strong> {answerText}</p> : null}
      </div>

      <div className="question-card slim">
        <p className="label">Current question</p>
        <h2>{question?.question_text ?? "Interview complete. You can leave for feedback."}</h2>
        <div className="question-actions">
          <button className="ghost compact" onClick={onSpeakQuestion}><Volume2 size={16} />Repeat</button>
          <button className="secondary compact" onClick={onSubmitTranscript}><Send size={16} />Submit answer</button>
          <button className="ghost compact" onClick={onNextQuestion}><Play size={16} />Next</button>
          <button className="ghost compact" onClick={onCodingRound}><Code2 size={16} />Coding</button>
          <button className="ghost compact" onClick={onSystemRound}><LayoutTemplate size={16} />Design</button>
          <button className="danger compact" onClick={onLeave}>Leave</button>
          {voiceMessage ? <span>{voiceMessage}</span> : null}
        </div>
      </div>

      <section className="transcript compact-transcript">
        <button className="transcript-toggle" onClick={onToggleTranscript}>
          Transcript
          <span>{transcriptOpen ? "Hide" : "Show"}</span>
        </button>
        {transcriptOpen ? (
          <div className="transcript-body">
            <div className="transcript-feed">
              {conversationMessages.map((message) => (
                <div className={`transcript-line ${message.speaker}`} key={message.id}>
                  <strong>{message.speaker === "candidate" ? setup.candidateName : "Interviewer"}</strong>
                  <p>{message.text}</p>
                </div>
              ))}
            </div>
            <textarea
              value={answerText}
              onChange={(event) => onAnswerText(event.target.value)}
              placeholder="Speech-to-text appears here while you answer."
            />
          </div>
        ) : null}
      </section>

      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}

function CodingRound({ onBack }) {
  return (
    <section className="coding-layout mock-coding">
      <BrandBar />
      <PhaseRail active="Coding" />
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
    <label className="field select-row">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option}>{option}</option>
        ))}
      </select>
      <ChevronDown className="select-chevron" size={18} />
    </label>
  );
}

function TextInputGroup({ label, value, onChange, readonly = false }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        readOnly={readonly}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
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

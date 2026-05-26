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
  Hand,
  LayoutTemplate,
  Mic,
  Moon,
  Play,
  Send,
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
const roleLibrary = [
  "Full Stack Developer",
  "Software Engineer",
  "AI Engineer",
  "Backend Developer",
  "Frontend Developer",
  "Data Analyst",
  "Data Scientist",
  "Cybersecurity Analyst",
  "Product Manager",
  "Business Analyst",
  "Project Manager",
  "Web Designer",
];
const roleTabs = ["Role Based", "Company Based", "JD Based", "Resume Toolkit", "Create Your Own"];
const experiences = ["Fresher", "Experienced", "Intern"];
const interviewTypes = [
  "Full Interview (45 mins)",
  "Technical",
  "Coding Interview",
  "HR",
  "System Design",
];
const companyStyles = ["FAANG", "Startup", "Indian Product"];
const interviewers = ["Payal", "Emma", "John", "Kapil"];
const interviewerProfiles = {
  Payal: { accent: "Indian English", style: "Warm technical mentor", initial: "P" },
  Emma: { accent: "US English", style: "Calm product interviewer", initial: "E" },
  John: { accent: "US English", style: "Senior engineering manager", initial: "J" },
  Kapil: { accent: "Indian English", style: "Strict technical lead", initial: "K" },
};
const personalities = ["Easy Going", "Friendly", "Strict", "FAANG pressure"];
const accents = ["US American", "Indian English", "British English"];
const liveStages = ["Intro", "Clarify", "Discuss", "Coding", "Testing", "Complexity", "Outro"];
const roundOptions = [
  {
    value: "Technical",
    title: "Role Related",
    subtitle: "Technical",
    detail: "Project depth, implementation tradeoffs, debugging, and production readiness.",
  },
  {
    value: "Coding Interview",
    title: "Coding",
    subtitle: "Programming",
    detail: "Algorithm questions with an editor, tests, terminal output, and approach discussion.",
  },
  {
    value: "HR",
    title: "Behavioral",
    subtitle: "HR",
    detail: "Communication, ownership, collaboration, and leadership examples.",
  },
  {
    value: "System Design",
    title: "System Design",
    subtitle: "Architecture",
    detail: "APIs, data model, scaling, bottlenecks, and failure handling.",
  },
];
const durationOptions = [
  { label: "5 mins", minutes: 5, premium: false },
  { label: "15 mins", minutes: 15, premium: true },
  { label: "30 mins", minutes: 30, premium: true },
];

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
  const isAwaitingAiResponseRef = useRef(false);
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
  const [isAwaitingAiResponse, setIsAwaitingAiResponse] = useState(false);
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
    experience: "Fresher",
    interviewType: "Full Interview (45 mins)",
    companyStyle: "Indian Product",
    interviewer: "John",
    personality: "Easy Going",
    accent: "US American",
    candidateName: "Harsh Raj",
    durationMinutes: 5,
    location: "India",
    education: "",
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
    isAwaitingAiResponseRef.current = isAwaitingAiResponse;
  }, [isAwaitingAiResponse]);

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

  function finalizeStreamingMessage(messageId, speaker, text) {
    if (!messageId || !text) return;
    setConversationMessages((current) => {
      const existing = current.find((item) => item.id === messageId);
      if (!existing) {
        return [
          ...current,
          {
            id: messageId,
            speaker,
            text,
            isStreaming: false,
          },
        ];
      }

      return current.map((item) =>
        item.id === messageId ? { ...item, text, isStreaming: false } : item,
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
          interviewer_accent: interviewerProfiles[setup.interviewer]?.accent ?? setup.accent,
          interview_duration_minutes: setup.durationMinutes,
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
      if (normalizeInterviewMode(setup.interviewType) === "system_design") {
        setScreen("system");
      } else if (normalizeInterviewMode(setup.interviewType) === "dsa") {
        setScreen("coding");
      } else {
        setScreen("live");
      }
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
      setVoiceMessage("Wait for the interviewer to finish, or use Interrupt.");
      return;
    }

    if (isAwaitingAiResponseRef.current) {
      setVoiceMessage("Interviewer is preparing the next response.");
      return;
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

  function interruptInterviewer() {
    if (!stream) {
      setError("Enable camera and microphone first.");
      return;
    }
    window.speechSynthesis?.cancel();
    isSpeakingRef.current = false;
    setIsSpeaking(false);
    if (!isRecordingRef.current && !isAwaitingAiResponseRef.current) {
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      recorder.start();
      transcriptStartedAtRef.current = Date.now();
      isRecordingRef.current = true;
      startSpeechRecognition();
      setIsRecording(true);
      setStatus("Recording answer");
    }
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
      if (isSpeakingRef.current || isAwaitingAiResponseRef.current) {
        return;
      }
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
    const voice = selectVoiceForAccent(setupRef.current?.accent);
    if (voice) utterance.voice = voice;
    utterance.lang = voice?.lang ?? accentToLang(setupRef.current?.accent);
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
    if (isSpeakingRef.current || isAwaitingAiResponseRef.current) return;

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
    if (isSubmittingTranscriptRef.current || isAwaitingAiResponseRef.current) return;
    isSubmittingTranscriptRef.current = true;
    isAwaitingAiResponseRef.current = true;
    setIsAwaitingAiResponse(true);
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
      isAwaitingAiResponseRef.current = false;
      setIsAwaitingAiResponse(false);
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
        if (event.payload.message_role === "generation_locked") {
          setVoiceMessage("Interviewer is still responding. I ignored a duplicate answer event.");
          return;
        }
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
        finalizeStreamingMessage(
          event.payload.message_id,
          "interviewer",
          followup,
        );
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
        isAwaitingAiResponseRef.current = false;
        setIsAwaitingAiResponse(false);
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
    isAwaitingAiResponseRef.current = false;
    setIsRecording(false);
    setIsListening(false);
    setIsSpeaking(false);
    setIsAwaitingAiResponse(false);
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
          onSelectRole={(role) => {
            updateSetup("role", role);
            setScreen("setup");
          }}
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
          onInterrupt={interruptInterviewer}
        />
      ) : null}

      {screen === "coding" ? (
        <CodingRound question={question} onBack={() => setScreen("live")} />
      ) : null}
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
  if (value === "Coding Interview") return "dsa";
  return value.toLowerCase().replace(" ", "_");
}

function selectedInterviewerName(setup) {
  return setup.interviewer || "John";
}

function accentToLang(accent) {
  if (accent === "British English") return "en-GB";
  if (accent === "US American" || accent === "US English") return "en-US";
  return "en-IN";
}

function selectVoiceForAccent(accent) {
  if (!window.speechSynthesis?.getVoices) return null;
  const voices = window.speechSynthesis.getVoices();
  const preferredLang = accentToLang(accent);
  return (
    voices.find((voice) => voice.lang === preferredLang && /female|neural|natural/i.test(voice.name))
    || voices.find((voice) => voice.lang === preferredLang)
    || voices.find((voice) => voice.lang?.startsWith(preferredLang.slice(0, 2)))
    || null
  );
}

function buildResumeContext(setup) {
  if (!setup.resumeName && !setup.resumeContext) return null;
  return [
    setup.resumeContext || `Resume file uploaded: ${setup.resumeName}.`,
    `Interview target: ${setup.role}, ${setup.companyStyle}, ${setup.experience}.`,
    `Candidate context: located in ${setup.location}; education: ${setup.education || "not provided"}.`,
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

function LandingScreen({ onStart, onSelectRole, theme, onToggleTheme }) {
  const [activeTab, setActiveTab] = useState("Role Based");
  const [roleSearch, setRoleSearch] = useState("");
  const filteredRoles = roleLibrary.filter((role) =>
    role.toLowerCase().includes(roleSearch.toLowerCase()),
  );

  return (
    <section className="landing">
      <nav className="nav">
        <strong>viewBuddy.ai</strong>
        <div className="nav-links">
          <span>Use Cases</span>
          <span>Resources</span>
          <span>Pricing</span>
          <span>Contact Us</span>
        </div>
        <div className="nav-actions">
          <ThemeToggle theme={theme} onToggleTheme={onToggleTheme} />
          <button className="ghost compact" onClick={onStart}>Sign up</button>
        </div>
      </nav>

      <section className="role-hero">
        <div className="role-tabs">
          {roleTabs.map((tab) => (
            <button
              className={activeTab === tab ? "role-tab active" : "role-tab"}
              key={tab}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
        <p className="pill">3000+ roles available</p>
        <h1>
          Role-Specific
          <span> AI Mock Interviews</span>
        </h1>
        <p className="hero-copy">
          Practice role-specific interviews with realistic questions, voice-based
          interviewer flow, coding rounds, and instant feedback reports.
        </p>
        <div className="role-search">
          <input
            value={roleSearch}
            onChange={(event) => setRoleSearch(event.target.value)}
            placeholder="Search for roles, e.g. Software Engineer, Data Analyst"
          />
          <button className="primary" onClick={onStart}>Search</button>
        </div>
      </section>

      <section className="section-band">
        <SectionTitle title="Roles" />
        <div className="role-grid">
          {filteredRoles.map((role) => (
            <button className="role-card" key={role} onClick={() => onSelectRole(role)}>
              {role}
            </button>
          ))}
        </div>
      </section>
    </section>
  );
}

function SetupScreen({ setup, interviewerTone, onChange, onResumeFile, onNext }) {
  const selectedRound = roundOptions.find((round) => round.value === setup.interviewType)
    ?? roundOptions[0];

  return (
    <section className="details-shell">
      <div className="details-header">
        <p className="eyebrow">Interview Details</p>
        <h1>{setup.role}</h1>
        <span>{selectedRound.title}</span>
      </div>

      <div className="details-grid">
        <section className="details-card wide-card">
          <div className="section-heading-row">
            <div>
              <h2>Resume Based Interview</h2>
              <p className="muted-copy">Upload a resume for personalized follow-up questions.</p>
            </div>
            <label className={setup.resumeName ? "upload-button has-file" : "upload-button"}>
              <FileText size={18} />
              {setup.resumeName || "Upload Resume"}
              <input
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={(event) => onResumeFile(event.target.files?.[0])}
              />
            </label>
          </div>
        </section>

        <section className="details-card wide-card">
          <SectionTitle title="Select Round" />
          <div className="round-grid">
            {roundOptions.map((round) => (
              <button
                className={setup.interviewType === round.value ? "option-card active" : "option-card"}
                key={round.value}
                onClick={() => onChange("interviewType", round.value)}
              >
                <strong>{round.title}</strong>
                <span>{round.subtitle}</span>
              </button>
            ))}
          </div>
          <div className="round-description">
            <strong>{selectedRound.title}</strong>
            <span>{selectedRound.detail}</span>
          </div>
        </section>

        <section className="details-card">
          <SectionTitle title="Difficulty Level" />
          <div className="segmented-options">
            {experiences.map((experience) => (
              <button
                className={setup.experience === experience ? "chip active" : "chip"}
                key={experience}
                onClick={() => onChange("experience", experience)}
              >
                {experience}
              </button>
            ))}
          </div>
        </section>

        <section className="details-card">
          <SectionTitle title="Interview Duration" />
          <div className="segmented-options">
            {durationOptions.map((duration) => (
              <button
                className={setup.durationMinutes === duration.minutes ? "chip active" : "chip"}
                key={duration.minutes}
                onClick={() => onChange("durationMinutes", duration.minutes)}
              >
                {duration.label}
                {duration.premium ? " Premium" : ""}
              </button>
            ))}
          </div>
        </section>

        <section className="details-card wide-card">
          <SectionTitle title="Select Your Interviewer" />
          <div className="interviewer-grid">
            {interviewers.map((name) => {
              const profile = interviewerProfiles[name];
              return (
                <button
                  className={setup.interviewer === name ? "interviewer-card active" : "interviewer-card"}
                  key={name}
                  onClick={() => {
                    onChange("interviewer", name);
                    onChange("accent", profile.accent);
                  }}
                >
                  <span className="mini-avatar">{profile.initial}</span>
                  <strong>{name}</strong>
                  <small>{profile.accent}</small>
                </button>
              );
            })}
          </div>
        </section>

        <section className="details-card">
          <SectionTitle title="Personalization" />
          <SelectGroup label="Role" value={setup.role} options={roles} onChange={(value) => onChange("role", value)} />
          <SelectGroup label="Company style" value={setup.companyStyle} options={companyStyles} onChange={(value) => onChange("companyStyle", value)} />
          <SelectGroup label="Personality" value={setup.personality} options={personalities} onChange={(value) => onChange("personality", value)} />
          <TextInputGroup label="Candidate name" value={setup.candidateName} onChange={(value) => onChange("candidateName", value)} />
        </section>

        <section className="details-card">
          <SectionTitle title="Profile Context" />
          <div className="profile-choice-list">
            {["India", "United States", "Other Country"].map((location) => (
              <button
                className={setup.location === location ? "profile-choice active" : "profile-choice"}
                key={location}
                onClick={() => onChange("location", location)}
              >
                {location}
              </button>
            ))}
          </div>
          <TextInputGroup
            label="College or school"
            value={setup.education}
            onChange={(value) => onChange("education", value)}
          />
        </section>

        <section className="details-card wide-card">
          <div className="premium-note">
            <Sparkles size={17} />
            <span>Premium roadmap: realistic neural voices, longer interviews, company-specific rounds, coding observation, replay analytics, and deeper resume memory.</span>
          </div>
        </section>

        <section className="details-actions">
          <button className="ghost" onClick={() => onResumeFile(null)}>Clear resume</button>
          <button className="primary" onClick={onNext}>Start Practice</button>
        </section>
      </div>

      <p className="setup-tone">{interviewerTone}</p>
    </section>
  );
}

function WaitingRoom({ stream, videoRef, setup, error, onEnableMedia, onStartInterview }) {
  const checklist = [
    "Interview setup completed.",
    "Your browser is compatible with our system.",
    stream ? "The microphone is enabled." : "Enable microphone before starting.",
    stream ? "The camera is enabled." : "Enable camera before starting.",
    "Use headphones for the best voice quality.",
    "Keep internet connection stable during the interview.",
  ];

  return (
    <section className="prereq-shell">
      <div className="prereq-top">
        <h1>Practice Prerequisite</h1>
        <button className="theme-toggle" aria-label="Close">x</button>
      </div>

      <div className="prereq-grid">
        <section className="prereq-card">
          <h2>Interview Instructions</h2>
          <div className="instruction-video">
            <VideoTile stream={stream} videoRef={videoRef} />
            {!stream ? <button className="primary compact" onClick={onEnableMedia}>Start Camera</button> : null}
          </div>
          {[
            "Wait for the AI interviewer introduction before answering.",
            "Use headphones or earphones for the best experience.",
            "Answer every question to receive a useful analytics report.",
            "Click Start Answer to record and End Answer when finished.",
          ].map((item, index) => (
            <div className="instruction-row" key={item}>
              <span>{index + 1}</span>
              {item}
            </div>
          ))}
        </section>

        <section className="prereq-card checklist-card">
          <div className="section-heading-row">
            <h2>Setup Checklist</h2>
            <span className="check-count">{stream ? "6/6" : "4/6"}</span>
          </div>
          <div className="checklist">
            {checklist.map((item, index) => (
              <div className="check-row" key={item}>
                <CheckCircle2 size={18} />
                <span>{item}</span>
                {index >= 2 && index <= 3 && !stream ? <small>Pending</small> : null}
              </div>
            ))}
          </div>
          {error ? <p className="error">{error}</p> : null}
          <button className="primary waiting-continue" disabled={!stream} onClick={onStartInterview}>
            Start Practice
          </button>
          {!stream ? (
            <button className="ghost waiting-continue" onClick={onEnableMedia}>
              Enable camera and mic
            </button>
          ) : null}
          <p className="muted-copy small">
            {setup.interviewer} will interview you in {interviewerProfiles[setup.interviewer]?.accent ?? setup.accent}.
          </p>
        </section>
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
      {liveStages.map((stage, index) => {
        const activeIndex = liveStages.indexOf(active);
        const isDone = index < activeIndex;
        return (
          <span
            className={`${stage === active ? "phase active" : "phase"} ${isDone ? "done" : ""}`}
            key={stage}
          >
            <span className="phase-dot" />
            {stage}
          </span>
        );
      })}
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

const codingProblem = {
  title: "Two Sum",
  prompt:
    "Given an array of integers nums and an integer target, return the indices of the two numbers such that they add up to target.",
  starter: `function solve(nums, target) {
  // Explain your approach first, then code.
  const seen = new Map();
  for (let index = 0; index < nums.length; index += 1) {
    const need = target - nums[index];
    if (seen.has(need)) return [seen.get(need), index];
    seen.set(nums[index], index);
  }
  return [];
}`,
  tests: [
    { input: [[2, 7, 11, 15], 9], expected: [0, 1] },
    { input: [[3, 2, 4], 6], expected: [1, 2] },
    { input: [[3, 3], 6], expected: [0, 1] },
  ],
};

function CodingRound({ question, onBack }) {
  const [code, setCode] = useState(codingProblem.starter);
  const [results, setResults] = useState([]);
  const [runtimeError, setRuntimeError] = useState("");
  const currentPrompt = question?.question_text || codingProblem.prompt;

  function runCode() {
    setRuntimeError("");
    setResults([]);
    try {
      // MVP-only browser runner. Production should move this into an isolated backend sandbox.
      const factory = new Function(`${code}; return solve;`);
      const solve = factory();
      if (typeof solve !== "function") {
        throw new Error("Define a function named solve.");
      }
      const nextResults = codingProblem.tests.map((test, index) => {
        const actual = solve(...structuredClone(test.input));
        const passed = JSON.stringify(actual) === JSON.stringify(test.expected);
        return {
          id: index + 1,
          passed,
          input: JSON.stringify(test.input),
          expected: JSON.stringify(test.expected),
          actual: JSON.stringify(actual),
        };
      });
      setResults(nextResults);
    } catch (caughtError) {
      setRuntimeError(caughtError.message);
    }
  }

  return (
    <section className="coding-layout mock-coding">
      <BrandBar />
      <PhaseRail active="Coding" />
      <div className="problem-panel">
        <SectionTitle title="Problem description" />
        <h2>{currentPrompt.includes("two") ? codingProblem.title : "Coding problem"}</h2>
        <p>{currentPrompt}</p>
        <ul className="tips">
          <li>First explain brute force and optimized approach out loud.</li>
          <li>Explain time and space complexity.</li>
          <li>Then implement `solve(nums, target)` in the editor.</li>
        </ul>
      </div>
      <div className="coding-interviewer">
        <Bot size={32} />
        <p>Before coding, walk me through your approach and edge cases. I will ask hints only after that.</p>
      </div>
      <div className="editor-panel">
        <div className="editor-toolbar">
          <span>JavaScript runner</span>
          <button className="primary compact" onClick={runCode}>
            <Play size={16} />
            Run tests
          </button>
        </div>
        <textarea
          className="code-editor"
          spellCheck="false"
          value={code}
          onChange={(event) => setCode(event.target.value)}
        />
      </div>
      <div className="terminal-panel">
        <SectionTitle title="Terminal" />
        {runtimeError ? (
          <pre className="terminal-error">Runtime error: {runtimeError}</pre>
        ) : null}
        {results.length ? (
          <div className="test-results">
            {results.map((result) => (
              <div className={result.passed ? "test-row passed" : "test-row failed"} key={result.id}>
                <strong>{result.passed ? "Passed" : "Failed"} test {result.id}</strong>
                <span>Input: {result.input}</span>
                <span>Expected: {result.expected}</span>
                <span>Actual: {result.actual}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-terminal">Run tests to see passed cases, failed cases, and runtime errors.</p>
        )}
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

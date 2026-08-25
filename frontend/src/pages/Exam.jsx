import Editor from "@monaco-editor/react";
import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import client from "../api/client";

const MONACO_LANGUAGE = { python: "python", java: "java", c: "c" };
const DIFFICULTY_PILL = { easy: "mooc-pill-easy", medium: "mooc-pill-medium", hard: "mooc-pill-hard" };

export default function Exam() {
  const { courseId } = useParams();
  const [phase, setPhase] = useState("loading"); // loading | idle | in_progress | completed
  const [courseKey, setCourseKey] = useState("python");
  const [attempt, setAttempt] = useState(null);
  const [answers, setAnswers] = useState({}); // problem_id -> code
  const [remaining, setRemaining] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const finalizedRef = useRef(false);

  useEffect(() => {
    client.get("/courses").then((res) => {
      const c = res.data.find((x) => x.id === Number(courseId));
      if (c) setCourseKey(c.key);
    });

    // Resume an in-progress attempt after navigating away and back, instead of
    // leaving it orphaned server-side with no way back in.
    client
      .get("/exam/current", { params: { course_id: courseId } })
      .then((res) => {
        if (res.data.attempt) {
          resumeAttempt(res.data.attempt);
        } else {
          setPhase("idle");
        }
      })
      .catch(() => setPhase("idle"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [courseId]);

  function resumeAttempt(attemptData) {
    setAttempt(attemptData);
    const initialAnswers = {};
    for (const q of attemptData.questions) {
      initialAnswers[q.id] = q.starter_code;
    }
    setAnswers(initialAnswers);
    finalizedRef.current = false;
    setPhase("in_progress");
  }

  useEffect(() => {
    if (phase !== "in_progress" || !attempt) return;

    const deadline = new Date(attempt.started_at).getTime() + attempt.duration_seconds * 1000;

    const tick = () => {
      const secondsLeft = Math.max(0, Math.round((deadline - Date.now()) / 1000));
      setRemaining(secondsLeft);
      if (secondsLeft <= 0 && !finalizedRef.current) {
        finalizedRef.current = true;
        handleFinalize();
      }
    };

    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase, attempt]);

  async function handleStart() {
    setStarting(true);
    setError("");
    setResult(null);
    try {
      const res = await client.post("/exam/start", { course_id: Number(courseId) });
      resumeAttempt(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Could not start the exam");
    } finally {
      setStarting(false);
    }
  }

  function updateAnswer(problemId, code) {
    setAnswers((prev) => ({ ...prev, [problemId]: code }));
  }

  async function handleFinalize() {
    if (submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        answers: Object.entries(answers).map(([problemId, code]) => ({
          problem_id: Number(problemId),
          code,
        })),
      };
      const res = await client.post(`/exam/${attempt.attempt_id}/finalize`, payload);
      setResult(res.data);
      setPhase("completed");
    } catch (err) {
      setError(err.response?.data?.error || "Could not submit the exam");
    } finally {
      setSubmitting(false);
    }
  }

  if (phase === "loading") {
    return <div className="mooc-page pt-4 text-body-secondary">Loading...</div>;
  }

  if (phase === "idle") {
    return (
      <div className="mooc-page pt-4" style={{ maxWidth: 640 }}>
        <Link to={`/courses/${courseId}`} className="btn btn-outline-primary btn-sm mb-3">
          ← Back to Course
        </Link>
        <span className="mooc-eyebrow d-block">Assessment</span>
        <h2 className="mooc-page-title mb-3">Final Exam</h2>
        <div className="card">
          <div className="card-body">
            <ul className="mb-4 ps-3" style={{ lineHeight: 1.9 }}>
              <li><strong>3 questions</strong> — one per difficulty</li>
              <li><strong>15 minute</strong> timer, enforced on the server too</li>
              <li>Pass with an overall score of <strong>60% or higher</strong></li>
              <li>Fail, and all three practice levels reset — redo them before retrying</li>
            </ul>
            {error && <div className="alert alert-danger">{error}</div>}
            <button className="btn btn-primary" onClick={handleStart} disabled={starting}>
              {starting ? "Starting..." : "Start Exam"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (phase === "in_progress") {
    const minutes = String(Math.floor(remaining / 60)).padStart(2, "0");
    const seconds = String(remaining % 60).padStart(2, "0");
    const urgent = remaining <= 60;

    return (
      <div className="mooc-page pt-4" style={{ maxWidth: 1000 }}>
        <div className="d-flex justify-content-between align-items-center mb-4">
          <div>
            <span className="mooc-eyebrow">In progress</span>
            <h2 className="mooc-page-title mb-0">Exam</h2>
          </div>
          <span
            className="font-mono fw-bold px-3 py-2 rounded-3"
            style={{
              fontSize: "1.4rem",
              color: urgent ? "var(--mooc-hard)" : "var(--mooc-text)",
              background: urgent ? "var(--mooc-hard-soft)" : "var(--mooc-surface)",
              border: "1px solid var(--mooc-border-soft)",
            }}
          >
            ⏱ {minutes}:{seconds}
          </span>
        </div>

        {error && <div className="alert alert-danger">{error}</div>}

        {attempt.questions.map((q, idx) => (
          <div className="card mb-4" key={q.id}>
            <div className="card-body">
              <div className="mb-2">
                <span className="text-body-secondary small me-2">Q{idx + 1}</span>
                <span className={`badge ${DIFFICULTY_PILL[q.difficulty]} text-capitalize me-2`}>
                  {q.difficulty}
                </span>
                <h5 className="d-inline mb-0">{q.title}</h5>
                <p className="mt-2 mb-0" style={{ whiteSpace: "pre-wrap" }}>{q.description}</p>
              </div>
              <div className="mooc-editor-shell mt-2">
                <Editor
                  height="220px"
                  language={MONACO_LANGUAGE[courseKey] || courseKey}
                  value={answers[q.id] || ""}
                  onChange={(value) => updateAnswer(q.id, value ?? "")}
                  theme="vs-dark"
                  options={{ fontFamily: "JetBrains Mono, monospace", fontSize: 13 }}
                />
              </div>
            </div>
          </div>
        ))}

        <button className="btn btn-success mb-5" onClick={handleFinalize} disabled={submitting}>
          {submitting ? "Submitting..." : "Submit Exam"}
        </button>
      </div>
    );
  }

  // completed
  if (!result) return <div className="mooc-page pt-4 text-body-secondary">Loading...</div>;

  return (
    <div className="mooc-page pt-4" style={{ maxWidth: 700 }}>
      <Link to={`/courses/${courseId}`} className="btn btn-outline-primary btn-sm mb-3">
        ← Back to Course
      </Link>
      <div className="text-center mb-4">
        <div className={`mooc-result-badge ${result.verdict === "PASS" ? "pass" : "fail"}`}>
          {result.verdict === "PASS" ? "✓" : "✕"}
        </div>
        <h2 className="mooc-page-title mb-1">
          {result.verdict === "PASS" ? "🎉 Exam passed — you're certified!" : "Exam not passed this time"}
        </h2>
        <p className="text-body-secondary">
          {result.verdict === "PASS"
            ? `Great work — you scored ${result.score}%. Your certificate is ready.`
            : `You scored ${result.score}%, and needed 60%+. All three practice levels have been reset — complete them again to unlock a brand-new exam set.`}
        </p>
      </div>

      <div className="card">
        <div className="card-body">
          <table className="table table-sm mb-0">
            <thead>
              <tr>
                <th className="ps-3">Question</th>
                <th>Verdict</th>
                <th className="pe-3">Score</th>
              </tr>
            </thead>
            <tbody>
              {result.per_question.map((q, i) => (
                <tr key={i}>
                  <td className="ps-3">{q.title || `Problem #${q.problem_id}`}</td>
                  <td>
                    <span className={`badge ${q.verdict === "PASS" ? "mooc-pill-easy" : "mooc-pill-hard"}`}>
                      {q.verdict}
                    </span>
                  </td>
                  <td className="pe-3">{q.score}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="d-flex gap-2 mt-3 justify-content-center">
        {result.verdict === "PASS" ? (
          <Link to={`/courses/${courseId}/certificate`} className="btn btn-primary">
            🏆 View Certificate
          </Link>
        ) : (
          <Link to={`/courses/${courseId}`} className="btn btn-primary">
            Restart Practice Levels
          </Link>
        )}
      </div>
    </div>
  );
}

import Editor from "@monaco-editor/react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../api/client";

const MONACO_LANGUAGE = { python: "python", java: "java", c: "c" };
const DIFFICULTY_PILL = { easy: "mooc-pill-easy", medium: "mooc-pill-medium", hard: "mooc-pill-hard" };

export default function Solve() {
  const { courseId, id } = useParams();
  const navigate = useNavigate();
  const [problem, setProblem] = useState(null);
  const [courseKey, setCourseKey] = useState("python");
  const [code, setCode] = useState("");
  const [result, setResult] = useState(null);
  const [hint, setHint] = useState("");
  const [running, setRunning] = useState(false);
  const [hintLoading, setHintLoading] = useState(false);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [siblingIds, setSiblingIds] = useState({ prevId: null, nextId: null });

  useEffect(() => {
    // Reset per-problem state immediately so the previous problem's verdict/hint
    // don't stay visible while the new problem is loading (or after it loads).
    setProblem(null);
    setResult(null);
    setError("");
    setHint("");
    setLoadError("");

    client
      .get(`/problems/${id}`)
      .then((res) => {
        setProblem(res.data);
        setCode(res.data.starter_code);

        client.get("/courses").then((coursesRes) => {
          const c = coursesRes.data.find((x) => x.id === Number(courseId));
          if (c) setCourseKey(c.key);
        });

        client
          .get("/problems", { params: { course_id: courseId, difficulty: res.data.difficulty } })
          .then((listRes) => {
            const ids = listRes.data.map((p) => p.id);
            const index = ids.indexOf(Number(id));
            setSiblingIds({
              prevId: index > 0 ? ids[index - 1] : null,
              nextId: index >= 0 && index < ids.length - 1 ? ids[index + 1] : null,
            });
          });
      })
      .catch((err) => {
        setLoadError(err.response?.data?.error || "Could not load this problem.");
      });
  }, [id, courseId]);

  async function handleRun() {
    setRunning(true);
    setError("");
    setResult(null);
    try {
      const res = await client.post("/submit", { problem_id: Number(id), code });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Submission failed");
    } finally {
      setRunning(false);
    }
  }

  async function handleHint() {
    setHintLoading(true);
    setHint("");
    try {
      const res = await client.post("/ai/hint", { problem_id: Number(id), code });
      setHint(res.data.hint);
    } catch {
      setHint("Could not fetch a hint right now.");
    } finally {
      setHintLoading(false);
    }
  }

  if (loadError) {
    return (
      <div className="mooc-page pt-4" style={{ maxWidth: 640 }}>
        <Link to={`/courses/${courseId}/practice`} className="btn btn-outline-primary btn-sm mb-3">
          ← Back to Practice
        </Link>
        <div className="alert alert-warning">🔒 {loadError}</div>
      </div>
    );
  }

  if (!problem) return <div className="mooc-page pt-4 text-body-secondary">Loading...</div>;

  return (
    <div className="mooc-page pt-4" style={{ maxWidth: 1280 }}>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <Link to={`/courses/${courseId}/practice`} className="btn btn-outline-primary btn-sm">
          ← Back to Practice
        </Link>
        <div className="d-flex gap-2">
          <button
            className="btn btn-outline-primary btn-sm"
            disabled={!siblingIds.prevId}
            onClick={() => navigate(`/courses/${courseId}/solve/${siblingIds.prevId}`)}
          >
            ← Previous
          </button>
          <button
            className="btn btn-outline-primary btn-sm"
            disabled={!siblingIds.nextId}
            onClick={() => navigate(`/courses/${courseId}/solve/${siblingIds.nextId}`)}
          >
            Next →
          </button>
        </div>
      </div>
      <div className="row g-4">
        <div className="col-lg-5">
          <span className={`badge ${DIFFICULTY_PILL[problem.difficulty]} text-capitalize mb-2`}>
            {problem.difficulty}
          </span>
          <h2 className="mooc-page-title mb-3">{problem.title}</h2>
          <div className="card">
            <div className="card-body">
              <p className="mb-0" style={{ whiteSpace: "pre-wrap" }}>
                {problem.description}
              </p>
            </div>
          </div>

          <div className="mt-3">
            <button className="btn btn-outline-info btn-sm" onClick={handleHint} disabled={hintLoading}>
              {hintLoading ? "Thinking..." : "✨ Get AI Hint"}
            </button>
            {hint && <div className="alert alert-info small mt-2 mb-0">{hint}</div>}
          </div>
        </div>

        <div className="col-lg-7">
          <div className="d-flex justify-content-end align-items-center mb-2">
            <button className="btn btn-success btn-sm" onClick={handleRun} disabled={running}>
              {running ? "Running..." : "▶ Run / Submit"}
            </button>
          </div>

          <div className="mooc-editor-shell">
            <Editor
              height="400px"
              language={MONACO_LANGUAGE[courseKey] || courseKey}
              value={code}
              onChange={(value) => setCode(value ?? "")}
              theme="vs-dark"
              options={{ fontFamily: "JetBrains Mono, monospace", fontSize: 14, padding: { top: 14 } }}
            />
          </div>

          {error && <div className="alert alert-danger mt-3">{error}</div>}

          {result && (
            <div className="mt-3">
              <div className="d-flex align-items-center gap-2 mb-2">
                <span className={`badge ${result.verdict === "PASS" ? "mooc-pill-easy" : "mooc-pill-hard"}`}>
                  {result.verdict}
                </span>
                <span className="text-body-secondary small">
                  {result.passed_count}/{result.total_count} test cases passed · {result.score}%
                </span>
              </div>
              <div className="card">
                <table className="table table-sm mb-0">
                  <thead>
                    <tr>
                      <th className="ps-3">#</th>
                      <th>Status</th>
                      <th>Expected</th>
                      <th className="pe-3">Actual</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.cases.map((c) => (
                      <tr key={c.case_index}>
                        <td className="ps-3">{c.case_index + 1}</td>
                        <td>
                          <span className={`badge ${c.passed ? "mooc-pill-easy" : "mooc-pill-hard"}`}>
                            {c.passed ? "Pass" : c.status}
                          </span>
                        </td>
                        <td><code>{c.expected_output}</code></td>
                        <td className="pe-3"><code>{c.actual_output || c.stderr || c.compile_output}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

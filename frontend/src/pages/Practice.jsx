import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import client from "../api/client";

const LEVELS = [
  { key: "easy", pill: "mooc-pill-easy" },
  { key: "medium", pill: "mooc-pill-medium" },
  { key: "hard", pill: "mooc-pill-hard" },
];

export default function Practice() {
  const { courseId } = useParams();
  const [searchParams] = useSearchParams();
  const [difficulty, setDifficulty] = useState(searchParams.get("difficulty") || "easy");
  const [course, setCourse] = useState(null);
  const [problems, setProblems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get(`/courses/${courseId}`).then((res) => setCourse(res.data));
  }, [courseId]);

  useEffect(() => {
    if (!course) return;
    const unlocked = isUnlocked(difficulty, course);
    if (!unlocked) {
      setProblems([]);
      setError("");
      return;
    }
    client
      .get("/problems", { params: { course_id: courseId, difficulty } })
      .then((res) => setProblems(res.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to load problems"));
  }, [courseId, difficulty, course]);

  function isUnlocked(level, courseData) {
    const index = LEVELS.findIndex((l) => l.key === level);
    if (index === 0) return true;
    return LEVELS.slice(0, index).every((l) => courseData.levels[l.key]);
  }

  const unlocked = course ? isUnlocked(difficulty, course) : true;
  const previousLevel = (() => {
    const index = LEVELS.findIndex((l) => l.key === difficulty);
    return index > 0 ? LEVELS[index - 1].key : null;
  })();

  return (
    <div className="mooc-page pt-4">
      <Link to={`/courses/${courseId}`} className="btn btn-outline-primary btn-sm mb-3">
        ← Back to Course
      </Link>
      <span className="mooc-eyebrow d-block">Practice</span>
      <h2 className="mooc-page-title mb-4">Sharpen your skills</h2>

      <div className="d-flex gap-2 mb-4">
        {LEVELS.map((level) => {
          const levelUnlocked = course ? isUnlocked(level.key, course) : true;
          return (
            <button
              key={level.key}
              className={`btn btn-sm text-capitalize ${
                difficulty === level.key ? "btn-primary" : "btn-outline-primary"
              }`}
              onClick={() => setDifficulty(level.key)}
            >
              {!levelUnlocked && "🔒 "}
              {level.key}
            </button>
          );
        })}
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {!unlocked ? (
        <div className="card">
          <div className="card-body text-center py-5">
            <div style={{ fontSize: "2rem" }} className="mb-2">🔒</div>
            <p className="mb-0">
              Complete every <strong className="text-capitalize">{previousLevel}</strong> problem
              first to unlock <strong className="text-capitalize">{difficulty}</strong>.
            </p>
          </div>
        </div>
      ) : (
        <div className="row g-3">
          {problems.map((p) => (
            <div className="col-md-6 col-lg-4" key={p.id}>
              <Link to={`/courses/${courseId}/solve/${p.id}`} className="text-decoration-none">
                <div className="card mooc-card-hover h-100">
                  <div className="card-body">
                    <div className="d-flex justify-content-between align-items-start mb-2">
                      <span
                        className={`badge ${LEVELS.find((l) => l.key === p.difficulty)?.pill} text-capitalize`}
                      >
                        {p.difficulty}
                      </span>
                      {p.solved && <span className="badge mooc-pill-easy">Solved</span>}
                      {!p.solved && p.attempted && <span className="badge mooc-pill-medium">Attempted</span>}
                    </div>
                    <h5 className="card-title text-body mb-0">{p.title}</h5>
                  </div>
                </div>
              </Link>
            </div>
          ))}
          {problems.length === 0 && !error && (
            <p className="text-body-secondary">No problems in this level yet.</p>
          )}
        </div>
      )}
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import client from "../api/client";

const LEVELS = ["easy", "medium", "hard"];
const LEVEL_LABEL = { easy: "Easy", medium: "Medium", hard: "Hard" };

export default function CourseDetail() {
  const { courseId } = useParams();
  const [course, setCourse] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    client
      .get(`/courses/${courseId}`)
      .then((res) => setCourse(res.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to load course"));
  }, [courseId]);

  if (error) return <div className="mooc-page pt-4"><div className="alert alert-danger">{error}</div></div>;
  if (!course) return <div className="mooc-page pt-4 text-body-secondary">Loading...</div>;

  const steps = [...LEVELS, "exam"];

  return (
    <div className="mooc-page pt-4">
      <Link to="/courses" className="btn btn-outline-primary btn-sm mb-3">
        ← All courses
      </Link>
      <span className="mooc-eyebrow d-block">{course.tag}</span>
      <h1 className="mooc-page-title mb-1">{course.title}</h1>
      <p className="text-body-secondary mb-4" style={{ maxWidth: 620 }}>
        {course.description}
      </p>

      <div className="mooc-progress-track">
        {steps.map((step, i) => {
          let cls = "mooc-track-node";
          let icon = i + 1;
          if (step === "exam") {
            icon = "★";
            if (course.certified) cls += " done";
            else if (LEVELS.every((l) => course.levels[l])) cls += " current";
          } else {
            if (course.levels[step]) {
              cls += " done";
              icon = "✓";
            } else if (LEVELS.slice(0, i).every((l) => course.levels[l])) {
              cls += " current";
            }
          }
          return (
            <div key={step} style={{ display: "flex", alignItems: "center", flex: step === "exam" ? "0 0 auto" : 1 }}>
              <div className={cls}>
                <span>{icon}</span>
              </div>
              {i < steps.length - 1 && <div className="mooc-track-line" />}
            </div>
          );
        })}
      </div>
      <div className="mooc-track-labels mb-4">
        <span>Easy</span>
        <span>Medium</span>
        <span>Hard</span>
        <span>Exam</span>
      </div>

      <div className="row g-3 mb-4">
        {LEVELS.map((level, i) => {
          const unlocked = i === 0 || LEVELS.slice(0, i).every((l) => course.levels[l]);
          const done = course.levels[level];
          return (
            <div className="col-md-4" key={level}>
              <div className={`mooc-level-card ${unlocked ? "" : "locked"}`}>
                <div className="d-flex justify-content-between align-items-center">
                  <span className="font-mono fw-semibold">{LEVEL_LABEL[level]}</span>
                  <span className={`mooc-level-icon ${done ? "done" : unlocked ? "current" : ""}`}>
                    {done ? "✓" : unlocked ? "▶" : "🔒"}
                  </span>
                </div>
                <p className="text-body-secondary small mb-0">
                  Practice problems · solve all to complete this level
                </p>
                {unlocked ? (
                  <Link
                    to={`/courses/${courseId}/practice?difficulty=${level}`}
                    className={`btn btn-sm mt-1 ${done ? "btn-outline-primary" : "btn-primary"}`}
                  >
                    {done ? "Practice again" : "Start practice"}
                  </Link>
                ) : (
                  <button className="btn btn-outline-primary btn-sm mt-1" disabled>
                    Locked
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {(() => {
        const allDone = LEVELS.every((l) => course.levels[l]);
        let cls = "mooc-exam-card";
        if (!allDone) cls += " locked";
        if (course.certified) cls += " certified";

        return (
          <div className={cls}>
            {course.certified ? (
              <>
                <div>
                  <h3 className="mb-1" style={{ fontSize: "1.1rem" }}>🏆 Certified</h3>
                  <p className="text-body-secondary small mb-0" style={{ maxWidth: 480 }}>
                    You passed the final exam for {course.title}. Your certificate is ready.
                  </p>
                </div>
                <Link to={`/courses/${courseId}/certificate`} className="btn btn-primary">
                  View certificate
                </Link>
              </>
            ) : allDone ? (
              <>
                <div>
                  <h3 className="mb-1" style={{ fontSize: "1.1rem" }}>Final exam unlocked</h3>
                  <p className="text-body-secondary small mb-0" style={{ maxWidth: 480 }}>
                    3 randomly-selected questions — pass at 60%+ to earn your certificate. Fail, and
                    you'll redo all three levels before trying again with a new set.
                  </p>
                </div>
                <Link to={`/courses/${courseId}/exam`} className="btn btn-primary">
                  Start final exam
                </Link>
              </>
            ) : (
              <div>
                <h3 className="mb-1" style={{ fontSize: "1.1rem" }}>🔒 Final exam locked</h3>
                <p className="text-body-secondary small mb-0" style={{ maxWidth: 480 }}>
                  Complete Easy, Medium and Hard practice for this course to unlock the exam.
                </p>
              </div>
            )}
          </div>
        );
      })()}
    </div>
  );
}

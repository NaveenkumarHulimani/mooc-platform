import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";
import { getUser } from "../auth";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const user = getUser();

  useEffect(() => {
    client
      .get("/dashboard")
      .then((res) => setData(res.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to load dashboard"));
  }, []);

  if (error) return <div className="mooc-page pt-4"><div className="alert alert-danger">{error}</div></div>;
  if (!data) return <div className="mooc-page pt-4 text-body-secondary">Loading...</div>;

  const { stats, courses, certificates, exam_history } = data;

  return (
    <div className="mooc-page pt-4">
      <span className="mooc-eyebrow">Student dashboard</span>
      <h1 className="mooc-page-title mb-4">Welcome back, {user?.name}</h1>

      <div className="row g-3 mb-2">
        {[
          { num: `${stats.certificates_earned}/${stats.total_courses}`, label: "Certificates earned" },
          { num: `${stats.levels_completed}/${stats.total_levels}`, label: "Levels completed" },
          { num: stats.exam_attempts, label: "Exam attempts" },
          { num: stats.total_courses, label: "Courses available" },
        ].map((s) => (
          <div className="col-6 col-md-3" key={s.label}>
            <div className="mooc-stat-tile">
              <div className="mooc-stat-number">{s.num}</div>
              <div className="text-body-secondary small mt-1">{s.label}</div>
            </div>
          </div>
        ))}
      </div>

      <h2 className="mooc-page-title mt-5 mb-3 fs-5">Course progress</h2>
      <div className="d-flex flex-column gap-2">
        {courses.map((c) => (
          <Link
            key={c.course_id}
            to={`/courses/${c.course_id}`}
            className="card text-decoration-none mooc-card-hover"
          >
            <div className="card-body d-flex align-items-center gap-3 py-3">
              <span className="font-mono text-body" style={{ width: 200, flexShrink: 0 }}>
                {c.title}
              </span>
              <div className="mooc-mini-bar flex-grow-1 mb-0">
                <div
                  className="mooc-mini-bar-fill"
                  style={{
                    width: `${c.pct}%`,
                    background: c.certified ? "var(--mooc-easy)" : "var(--mooc-accent)",
                  }}
                />
              </div>
              <span className="text-body-secondary small font-mono" style={{ width: 42, textAlign: "right" }}>
                {c.pct}%
              </span>
            </div>
          </Link>
        ))}
      </div>

      <h2 className="mooc-page-title mt-5 mb-3 fs-5">Certificates earned</h2>
      {certificates.length === 0 ? (
        <p className="text-body-secondary font-mono small">No certificates yet — pass a final exam to earn one.</p>
      ) : (
        <div className="d-flex gap-3 flex-wrap">
          {certificates.map((cert) => (
            <Link
              key={cert.course_id}
              to={`/courses/${cert.course_id}/certificate`}
              className="text-decoration-none"
            >
              <div
                className="p-3 rounded-3"
                style={{
                  background: "var(--mooc-easy-soft)",
                  border: "1px solid var(--mooc-easy)",
                  color: "var(--mooc-easy)",
                }}
              >
                <div className="font-mono small">🏅 {cert.title}</div>
                <div className="font-mono" style={{ fontSize: "0.7rem", opacity: 0.8 }}>
                  {new Date(cert.issued_at).toLocaleDateString()}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      <h2 className="mooc-page-title mt-5 mb-3 fs-5">Exam history</h2>
      {exam_history.length === 0 ? (
        <p className="text-body-secondary font-mono small">No exam attempts yet.</p>
      ) : (
        <div className="card">
          <table className="table table-sm mb-0">
            <thead>
              <tr>
                <th className="ps-3">Course</th>
                <th>Date</th>
                <th>Score</th>
                <th className="pe-3">Result</th>
              </tr>
            </thead>
            <tbody>
              {exam_history.map((row, i) => (
                <tr key={i}>
                  <td className="ps-3">{row.course_title}</td>
                  <td className="text-body-secondary">{new Date(row.started_at).toLocaleDateString()}</td>
                  <td>{row.score}%</td>
                  <td className="pe-3">
                    <span className={`badge ${row.verdict === "PASS" ? "mooc-pill-easy" : "mooc-pill-hard"}`}>
                      {row.verdict === "PASS" ? "Passed" : "Failed"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

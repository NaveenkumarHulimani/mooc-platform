import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import client from "../api/client";

export default function Courses() {
  const [courses, setCourses] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    client
      .get("/courses")
      .then((res) => setCourses(res.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to load courses"));
  }, []);

  if (error) return <div className="mooc-page pt-4"><div className="alert alert-danger">{error}</div></div>;
  if (!courses) return <div className="mooc-page pt-4 text-body-secondary">Loading...</div>;

  return (
    <div className="mooc-page pt-4">
      <span className="mooc-eyebrow">Course catalog</span>
      <h1 className="mooc-page-title mb-4">Pick a course to practice</h1>

      <div className="mooc-course-grid">
        {courses.map((course) => {
          const doneCount = Object.values(course.levels).filter(Boolean).length;
          const pct = course.certified ? 100 : Math.round((doneCount / 3) * 100);
          return (
            <Link key={course.id} to={`/courses/${course.id}`} className="text-decoration-none">
              <div className="mooc-course-card mooc-card-hover">
                <span className="mooc-course-tag">{course.tag}</span>
                <h3 className="text-body mb-0" style={{ fontSize: "1.15rem" }}>
                  {course.title}
                </h3>
                <p className="text-body-secondary small mb-0">{course.description}</p>
                <div className="mooc-mini-bar">
                  <div className="mooc-mini-bar-fill" style={{ width: `${pct}%` }} />
                </div>
                <div className="d-flex gap-2 mt-auto">
                  <span className="badge bg-secondary">{doneCount}/3 levels</span>
                  {course.certified && <span className="badge mooc-pill-easy">Certified ✓</span>}
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import client from "../api/client";
import { getUser } from "../auth";

export default function Certificate() {
  const { courseId } = useParams();
  const [cert, setCert] = useState(null);
  const [course, setCourse] = useState(null);
  const [error, setError] = useState("");
  const [downloading, setDownloading] = useState(false);
  const user = getUser();

  useEffect(() => {
    client.get(`/courses/${courseId}`).then((res) => setCourse(res.data));
    client
      .get("/certificate", { params: { course_id: courseId } })
      .then((res) => setCert(res.data))
      .catch((err) => setError(err.response?.data?.error || "Failed to load certificate status"));
  }, [courseId]);

  async function handleDownload() {
    setDownloading(true);
    try {
      const res = await client.get("/certificate/download", {
        params: { course_id: courseId },
        responseType: "blob",
      });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${cert.cert_id}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      setError("Could not download the certificate right now.");
    } finally {
      setDownloading(false);
    }
  }

  if (error) return <div className="mooc-page pt-4"><div className="alert alert-danger">{error}</div></div>;
  if (!cert) return <div className="mooc-page pt-4 text-body-secondary">Loading...</div>;

  return (
    <div className="mooc-page pt-4" style={{ maxWidth: 820 }}>
      <Link to={`/courses/${courseId}`} className="btn btn-outline-primary btn-sm mb-3">
        ← Back to Course
      </Link>
      <span className="mooc-eyebrow d-block">Achievement</span>
      <h2 className="mooc-page-title mb-4">Certificate</h2>

      {!cert.has_certificate ? (
        <div className="card">
          <div className="card-body text-center py-5">
            <div style={{ fontSize: "2.5rem" }} className="mb-2">🔒</div>
            <p className="mb-3">
              You haven't earned this certificate yet. Pass the final exam for{" "}
              {course?.title || "this course"} to unlock it.
            </p>
            <Link to={`/courses/${courseId}/exam`} className="btn btn-primary">
              Go to Exam
            </Link>
          </div>
        </div>
      ) : (
        <>
          <div className="mooc-certificate">
            <p className="mooc-cert-mark">Coding MOOC · Certificate of Completion</p>
            <h1 className="mooc-cert-title">Certificate of Achievement</h1>
            <p className="text-body-secondary small">This certifies that</p>
            <p className="mooc-cert-name">{user?.name}</p>
            <p className="mx-auto" style={{ maxWidth: 520, lineHeight: 1.7 }}>
              has successfully completed all practice levels and passed the randomized final exam
              for <strong>{course?.title}</strong>, demonstrating proficiency in the core concepts
              of the course.
            </p>
            <div className="mooc-cert-footer">
              <div className="col">
                <div className="val">{new Date(cert.issued_at).toLocaleDateString()}</div>
                Date issued
              </div>
              <div className="col">
                <div className="val">{cert.score}%</div>
                Exam score
              </div>
              <div className="col">
                <div className="val">Coding MOOC</div>
                Issuing platform
              </div>
            </div>
            <p className="mooc-cert-id">Certificate ID: {cert.cert_id}</p>
          </div>
          <div className="text-center mt-4">
            <button className="btn btn-primary" onClick={handleDownload} disabled={downloading}>
              {downloading ? "Preparing..." : "⬇ Download PDF"}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

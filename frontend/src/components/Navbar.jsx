import { Link, useLocation, useNavigate } from "react-router-dom";
import { clearSession, getUser, isLoggedIn } from "../auth";

const LINKS = [
  { to: "/courses", label: "Courses" },
  { to: "/dashboard", label: "Dashboard" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const loggedIn = isLoggedIn();
  const user = getUser();

  function handleLogout() {
    clearSession();
    navigate("/login");
  }

  const initial = user?.name?.trim()?.[0]?.toUpperCase() || "?";

  return (
    <nav className="mooc-navbar d-flex align-items-center">
      <Link className="mooc-brand" to="/">
        <span className="mooc-brand-mark">{"{ }"}</span>
        Coding MOOC
      </Link>
      {loggedIn && (
        <div className="d-flex ms-auto align-items-center gap-4">
          <div className="d-none d-md-flex gap-4">
            {LINKS.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={`mooc-nav-link ${location.pathname.startsWith(link.to) ? "active" : ""}`}
              >
                {link.label}
              </Link>
            ))}
          </div>
          <div className="d-flex align-items-center gap-2">
            <span className="mooc-avatar">{initial}</span>
            <span className="text-body-secondary small d-none d-sm-inline">{user?.name}</span>
          </div>
          <button className="btn btn-outline-primary btn-sm" onClick={handleLogout}>
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}

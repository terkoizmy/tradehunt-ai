import { Routes, Route, Link, useLocation } from "react-router-dom";
import Home from "./pages/Home";
import Arena from "./pages/Arena";
import AgentProfile from "./pages/AgentProfile";
import Leaderboard from "./pages/Leaderboard";

function AppNavbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="nav-logo">
        <span className="prefix">&gt;_</span>
        <span className="name">
          Trading<span style={{ color: "var(--accent)" }}>Hunter</span>
        </span>
      </Link>
      <div className="nav-links">
        <Link to="/arena">Arena</Link>
        <Link to="/leaderboard">Leaderboard</Link>
      </div>
    </nav>
  );
}

export default function App() {
  const location = useLocation();
  const isLanding = location.pathname === "/";

  return (
    <div className="app">
      {!isLanding && <AppNavbar />}
      <Routes>
        <Route path="/" element={<Home />} />
        <Route
          path="/arena"
          element={
            <main className="main-content"><Arena /></main>
          }
        />
        <Route
          path="/agents/:id"
          element={
            <main className="main-content"><AgentProfile /></main>
          }
        />
        <Route
          path="/leaderboard"
          element={
            <main className="main-content"><Leaderboard /></main>
          }
        />
      </Routes>
    </div>
  );
}

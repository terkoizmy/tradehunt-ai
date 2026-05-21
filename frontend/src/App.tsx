import { Routes, Route, Link } from "react-router-dom";
import Home from "./pages/Home";
import Arena from "./pages/Arena";
import AgentProfile from "./pages/AgentProfile";
import Leaderboard from "./pages/Leaderboard";

function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="nav-logo">
        tradehunt.ai
      </Link>
      <div className="nav-links">
        <Link to="/arena">Arena</Link>
        <Link to="/leaderboard">Leaderboard</Link>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <div className="app">
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/arena" element={<Arena />} />
          <Route path="/agents/:id" element={<AgentProfile />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
        </Routes>
      </main>
    </div>
  );
}

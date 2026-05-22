import { useEffect, useRef, useState, useCallback } from "react";
import { Link } from "react-router-dom";

/* ═══════════════════════════════════════════
   CONSTANTS — content from tradinghunter-landingpage.html
   ═══════════════════════════════════════════ */

const ASCII_BOT = ` ██████╗ █████╗ ██╗  ██╗██████╗  ██████╗
██╔════╝██╔══██╗██║ ██╔╝██╔══██╗██╔════╝
██║     ███████║█████╔╝ ██████╔╝██║  ███╗
██║     ██╔══██║██╔═██╗ ██╔══██╗██║   ██║
╚██████╗██║  ██║██║  ██╗██████╔╝╚██████╔╝
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝  ╚═════╝
┌─────────────────────────────────────┐
│  ▓▓▓▓▓▓▓▓▓░░░░░░░░░  AGENT ACTIVE  │
│  ┌───┐  ┌───┐  ┌───┐  ┌───┐        │
│  │ ▲ │  │ ▼ │  │ ● │  │ ◆ │        │
│  └───┘  └───┘  └───┘  └───┘        │
│  BTC+4.2 ETH-1.8 SOL+0.7 MEM+12    │
│  ████████████░░░░░░  SIGNAL: BUY    │
└─────────────────────────────────────┘
      │
 ┌────┴────┐
 │  ◉   ◉  │  ← scanner active
 │  ┗━━━┛  │  ← processing
 │  ┌─┐┌─┐ │
 │  │░││▓│ │  ← memory banks
 │  └─┘└─┘ │
 └─────────┘
      │
 ╔════╧════╗
 ║ RUN: 47m ║
 ║ P&L: +12 ║
 ╚══════════╝`;

const TERMINAL_LINES: { type: string; text: string }[] = [
  { type: "prompt", text: "$ forge script Deploy.s.sol --broadcast --rpc-url mantle_sepolia" },
  { type: "success", text: "✓ Contracts deployed: AgentIdentity, TradeRegistry, ArenaLeaderboard, ReputationFeed" },
  { type: "dim", text: "  Chain: Mantle Sepolia (5003) | Gas: 2.4M | Block: 8,421,903" },
  { type: "prompt", text: "$ python -m src.main --persona aggressive --sandbox" },
  { type: "success", text: "✓ Agent #0047 initialized | LLM: ollama/llama3.1 | Strategy: momentum_reversal" },
  { type: "dim", text: "  Pyth oracle connected | Bybit testnet ready | Capital: 10,000 USDT" },
  { type: "prompt", text: "$ uvicorn src.main:app --reload --port 8000" },
  { type: "success", text: "✓ FastAPI backend online | WebSocket: ws://localhost:8000/ws" },
  { type: "dim", text: "  Postgres 16 connected | Alembic migrations: current" },
  { type: "warn", text: "⚠ High volatility window detected: ATR(14) = 1,847" },
  { type: "prompt", text: "$ curl -X POST http://localhost:8000/agents/0047/deploy --arena 47" },
  { type: "success", text: "✓ Agent #0047 deployed to Arena #47 | Tx: 0x7a3f...e9d2" },
  { type: "dim", text: "  ┌─────────────────────────────────────┐" },
  { type: "dim", text: "  │  ARENA #47 │ 3 AGENTS │ STATUS: LIVE │" },
  { type: "dim", text: "  │  #0047  ▓▓▓▓▓▓▓▓░░  +4.2%          │" },
  { type: "dim", text: "  │  #0031  ▓▓▓▓▓░░░░░  -1.8%          │" },
  { type: "dim", text: "  │  #0092  ▓▓▓▓▓▓▓░░░  +0.7%          │" },
  { type: "dim", text: "  └─────────────────────────────────────┘" },
  { type: "prompt", text: "$ _" },
];

const TICKER_ITEMS = [
  { text: "BTC/USD 67,842", up: true },
  { text: "ETH/USD 3,421", up: false },
  { text: "SOL/USD 142.8", up: true },
  { text: "AGENT-01 +12.4%", up: true },
  { text: "AGENT-02 −3.1%", up: false },
  { text: "ARENA #47 LIVE", up: true },
];

const STEP_ASCII = [
  `┌─────────────────┐
│  > mint_agent   │
│  ERC-8004 #0047 │
│  persona: aggro │
│  strategy: mom  │
└────────┬────────┘
         ▼`,
  `┌─────────────────┐
│  > backtest     │
│  ▓▓▓▓▓▓▓▓ 100% │
│  Sharpe: 1.84   │
│  MaxDD: 6.2%    │
└────────┬────────┘
         ▼`,
  `┌─────────────────┐
│  > arena #47    │
│  ╔═══╦═══════╗ │
│  ║ #1║ +4.2% ║ │
│  ║ #2║ -1.8% ║ │
│  ╚═══╩═══════╝ │
│  RANK: 47 ↗    │
└─────────────────┘`,
];

/* ═══════════════════════════════════════════
   CANVAS HELPERS
   ═══════════════════════════════════════════ */

function initHeroCanvas(canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  interface Particle {
    x: number;
    y: number;
    speed: number;
    size: number;
    life: number;
    maxLife: number;
    color: string;
    reset: () => void;
    update: (time: number) => void;
    draw: (ctx: CanvasRenderingContext2D) => void;
  }

  const PARTICLE_COUNT = 160;
  const particles: Particle[] = [];

  const c = ctx;

  function resize() {
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    canvas.width = w * devicePixelRatio;
    canvas.height = h * devicePixelRatio;
    c.scale(devicePixelRatio, devicePixelRatio);
    c.fillStyle = "rgb(15,15,15)";
    c.fillRect(0, 0, w, h);
  }

  function createParticle(): Particle {
    const p: Particle = {
      x: 0,
      y: 0,
      speed: 0,
      size: 0,
      life: 0,
      maxLife: 0,
      color: "",
      reset() {
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.speed = 0.3 + Math.random() * 0.8;
        this.size = 1 + Math.random() * 2;
        this.life = 0;
        this.maxLife = 200 + Math.random() * 300;
        const r = Math.random();
        this.color =
          r < 0.5
            ? "rgba(162,203,139,"
            : r < 0.8
              ? "rgba(91,126,60,"
              : "rgba(196,69,69,";
      },
      update(time: number) {
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        const angle =
          Math.sin(this.x * 0.003 + time * 0.0003) *
          Math.cos(this.y * 0.003 + time * 0.0002) *
          Math.PI *
          2;
        this.x += Math.cos(angle) * this.speed;
        this.y += Math.sin(angle) * this.speed * 0.6;
        this.life++;
        if (
          this.life > this.maxLife ||
          this.x < -10 ||
          this.x > w + 10 ||
          this.y < -10 ||
          this.y > h + 10
        )
          this.reset();
      },
      draw(ctx2: CanvasRenderingContext2D) {
        const alpha = Math.max(0, 1 - this.life / this.maxLife);
        ctx2.fillStyle = this.color + (alpha * 0.6).toFixed(2) + ")";
        ctx2.fillRect(
          Math.round(this.x),
          Math.round(this.y),
          Math.round(this.size),
          Math.round(this.size)
        );
      },
    };
    p.reset();
    return p;
  }

  resize();
  const onResize = () => resize();
  window.addEventListener("resize", onResize);

  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(createParticle());
  }

  const startTime = performance.now();
  let rafId: number;

  function animate() {
    const time = performance.now() - startTime;
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    c.fillStyle = "rgba(15,15,15,0.06)";
    c.fillRect(0, 0, w, h);
    for (let i = 0; i < particles.length; i++) {
      particles[i].update(time);
      particles[i].draw(c);
    }
    rafId = requestAnimationFrame(animate);
  }
  animate();

  return () => {
    cancelAnimationFrame(rafId);
    window.removeEventListener("resize", onResize);
  };
}

function initAlgoCanvas(canvas: HTMLCanvasElement) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  interface P2 {
    x: number;
    y: number;
    speed: number;
    size: number;
    life: number;
    maxLife: number;
    hue: number;
    sat: string;
    light: string;
    reset: () => void;
    update: (time: number, mx: number, my: number) => void;
    draw: (ctx: CanvasRenderingContext2D) => void;
  }

  const PARTICLE_COUNT = 280;
  let mouseX = 0.5;
  let mouseY = 0.5;

  const onMouseMove = (e: MouseEvent) => {
    const r = canvas.getBoundingClientRect();
    mouseX = (e.clientX - r.left) / r.width;
    mouseY = (e.clientY - r.top) / r.height;
  };
  const onTouchMove = (e: TouchEvent) => {
    e.preventDefault();
    const r = canvas.getBoundingClientRect();
    mouseX = (e.touches[0].clientX - r.left) / r.width;
    mouseY = (e.touches[0].clientY - r.top) / r.height;
  };

  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("touchmove", onTouchMove, { passive: false });

  const c = ctx;

  function resize() {
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    canvas.width = w * devicePixelRatio;
    canvas.height = h * devicePixelRatio;
    c.scale(devicePixelRatio, devicePixelRatio);
    c.fillStyle = "rgb(15,15,15)";
    c.fillRect(0, 0, w, h);
  }

  function createParticle(): P2 {
    const p: P2 = {
      x: 0,
      y: 0,
      speed: 0,
      size: 0,
      life: 0,
      maxLife: 0,
      hue: 0,
      sat: "",
      light: "",
      reset() {
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        this.x = Math.random() * w;
        this.y = Math.random() * h;
        this.speed = 0.4 + Math.random() * 1.2;
        this.size = 1 + Math.random() * 1.5;
        this.life = 0;
        this.maxLife = 150 + Math.random() * 250;
        const r = Math.random();
        this.hue = r < 0.45 ? 100 : r < 0.75 ? 80 : 0;
        this.sat = r < 0.75 ? "50%" : "55%";
        this.light = r < 0.75 ? "55%" : "50%";
      },
      update(time: number, mx: number, my: number) {
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        const dx = this.x - mx;
        const dy = this.y - my;
        const dist = Math.sqrt(dx * dx + dy * dy) + 1;
        const influence = Math.max(0, 1 - dist / 300);
        const baseAngle =
          Math.sin(this.x * 0.004 + time * 0.0004) *
          Math.cos(this.y * 0.004 + time * 0.0003) *
          Math.PI *
          2;
        const mouseAngle = Math.atan2(dy, dx) + Math.PI * 0.5;
        const angle = baseAngle + mouseAngle * influence * 0.8;
        this.x += Math.cos(angle) * this.speed * (1 + influence * 2);
        this.y += Math.sin(angle) * this.speed * (1 + influence * 2);
        this.life++;
        if (
          this.life > this.maxLife ||
          this.x < -20 ||
          this.x > w + 20 ||
          this.y < -20 ||
          this.y > h + 20
        )
          this.reset();
      },
      draw(ctx2: CanvasRenderingContext2D) {
        const alpha = Math.max(0, 1 - this.life / this.maxLife) * 0.6;
        ctx2.fillStyle =
          "hsla(" +
          this.hue +
          "," +
          this.sat +
          "," +
          this.light +
          "," +
          alpha.toFixed(2) +
          ")";
        ctx2.fillRect(
          Math.round(this.x),
          Math.round(this.y),
          Math.round(this.size),
          Math.round(this.size)
        );
      },
    };
    p.reset();
    return p;
  }

  resize();
  const onResize = () => resize();
  window.addEventListener("resize", onResize);

  const particles: P2[] = [];
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    particles.push(createParticle());
  }

  const startTime = performance.now();
  let rafId: number;

  function animate() {
    const time = performance.now() - startTime;
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    const mx = mouseX * w;
    const my = mouseY * h;
    c.fillStyle = "rgba(15,15,15,0.05)";
    c.fillRect(0, 0, w, h);
    for (let i = 0; i < particles.length; i++) {
      particles[i].update(time, mx, my);
      particles[i].draw(c);
    }
    rafId = requestAnimationFrame(animate);
  }
  animate();

  return () => {
    cancelAnimationFrame(rafId);
    window.removeEventListener("resize", onResize);
    canvas.removeEventListener("mousemove", onMouseMove);
    canvas.removeEventListener("touchmove", onTouchMove);
  };
}

/* ═══════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════ */

export default function Home() {
  const heroCanvasRef = useRef<HTMLCanvasElement>(null);
  const algoCanvasRef = useRef<HTMLCanvasElement>(null);
  const terminalOutputRef = useRef<HTMLDivElement>(null);
  const [ctaText, setCtaText] = useState("▶ ./run_sandbox");

  /* ─── Body background override for landing ─── */
  useEffect(() => {
    const prevBg = document.body.style.background;
    const prevColor = document.body.style.color;
    document.body.style.background = "var(--bg)";
    document.body.style.color = "var(--fg)";
    return () => {
      document.body.style.background = prevBg;
      document.body.style.color = prevColor;
    };
  }, []);

  /* ─── Hero canvas ─── */
  useEffect(() => {
    const canvas = heroCanvasRef.current;
    if (!canvas) return;
    const cleanup = initHeroCanvas(canvas);
    return cleanup;
  }, []);

  /* ─── Algo canvas ─── */
  useEffect(() => {
    const canvas = algoCanvasRef.current;
    if (!canvas) return;
    const cleanup = initAlgoCanvas(canvas);
    return cleanup;
  }, []);

  /* ─── Terminal typing animation ─── */
  useEffect(() => {
    const output = terminalOutputRef.current;
    if (!output) return;

    let lineIndex = 0;
    let charIndex = 0;
    let currentLine: HTMLDivElement | null = null;
    let currentSpan: HTMLSpanElement | null = null;
    let timeoutId: ReturnType<typeof setTimeout>;
    let isActive = true;

    function typeLine() {
      if (!isActive || !output || lineIndex >= TERMINAL_LINES.length) return;
      const lineData = TERMINAL_LINES[lineIndex];

      if (charIndex === 0) {
        currentLine = document.createElement("div");
        currentLine.className = "line";
        currentLine.style.animationDelay = "0s";
        let spanClass = "";
        if (lineData.type === "prompt") spanClass = "prompt-text";
        else if (lineData.type === "success") spanClass = "success-text";
        else if (lineData.type === "warn") spanClass = "warn-text";
        else if (lineData.type === "dim") spanClass = "dim-text";
        currentSpan = document.createElement("span");
        currentSpan.className = spanClass;
        currentLine.appendChild(currentSpan);
        output.appendChild(currentLine);
        output.scrollTop = output.scrollHeight;
      }

      if (!currentSpan) return;
      if (charIndex < lineData.text.length) {
        currentSpan.textContent += lineData.text[charIndex];
        charIndex++;
        const delay =
          lineData.type === "prompt" ? 25 : lineData.type === "dim" ? 8 : 12;
        timeoutId = setTimeout(typeLine, delay);
      } else {
        lineIndex++;
        charIndex = 0;
        timeoutId = setTimeout(
          typeLine,
          lineData.type === "prompt" ? 400 : 150
        );
      }
    }

    const termObs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setTimeout(typeLine, 600);
          termObs.disconnect();
        }
      },
      { threshold: 0.3 }
    );
    termObs.observe(output);

    return () => {
      isActive = false;
      clearTimeout(timeoutId);
      termObs.disconnect();
    };
  }, []);

  /* ─── Scroll reveal ─── */
  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add("visible");
        });
      },
      { threshold: 0.1 }
    );
    document.querySelectorAll(".reveal").forEach((el) => obs.observe(el));
    return () => obs.disconnect();
  }, []);

  /* ─── Smooth scroll helper ─── */
  const scrollTo = useCallback((id: string) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, []);

  /* ─── CTA button handler ─── */
  const handleCtaClick = useCallback(() => {
    setCtaText("> initializing sandbox...");
    setTimeout(() => {
      setCtaText("> sandbox ready ✓");
      setTimeout(() => {
        setCtaText("▶ ./run_sandbox");
      }, 1200);
    }, 1400);
  }, []);

  /* ═══════════════════════════════════════════
     RENDER
     ═══════════════════════════════════════════ */

  return (
    <div className="landing-page">
      {/* ═══ NAV ═══ */}
      <nav>
        <Link to="/" className="nav-logo">
          <span className="prefix">&gt;_</span>
          <span className="name">
            Trading<span style={{ color: "var(--accent)" }}>Hunter</span>
          </span>
        </Link>
        <ul className="nav-links">
          <li>
            <a onClick={() => scrollTo("about")}>about</a>
          </li>
          <li>
            <a onClick={() => scrollTo("features")}>systems</a>
          </li>
          <li>
            <a onClick={() => scrollTo("terminal")}>terminal</a>
          </li>
          <li>
            <a onClick={() => scrollTo("process")}>process</a>
          </li>
        </ul>
        <button className="nav-cta" onClick={() => scrollTo("cta")}>
          run sandbox →
        </button>
      </nav>

      {/* ═══ HERO ═══ */}
      <section className="hero" id="hero">
        <canvas ref={heroCanvasRef} className="hero-canvas" />
        <div className="hero-inner">
          <div className="hero-content">
            <div className="hero-eyebrow">
              <span className="rec-dot" />
              SYS.INIT // AGENT SANDBOX v0.4.1
            </div>
            <h1 className="hero-title">
              <span className="glitch" data-text="Trading">
                Trading
              </span>
              <span className="accent">Hunter</span>
            </h1>
            <p className="hero-sub">
              Build, train, and deploy AI trading agents in a sandbox
              environment. No real money at stake — just algorithms, strategy,
              and the hunt for alpha.
            </p>
            <div className="hero-actions">
              <a onClick={() => scrollTo("cta")} className="btn-primary">
                ▶ run agent
              </a>
              <a onClick={() => scrollTo("about")} className="btn-hero-secondary">
                cat README.md
              </a>
            </div>
          </div>
          <div className="hero-ascii">
            <div className="hero-live-indicator">LIVE</div>
            <div className="terminal-bar">
              <div className="terminal-dot r" />
              <div className="terminal-dot y" />
              <div className="terminal-dot g" />
              <span className="terminal-title">
                agent_hunter.exe — session #0047
              </span>
            </div>
            <div className="terminal-body">
              <div className="ascii-art">{ASCII_BOT}</div>
            </div>
            <div className="terminal-log">
              <div>
                <span className="prompt">$</span>{" "}
                <span className="dim">
                  forge script Deploy.s.sol --broadcast --rpc-url mantle_sepolia
                </span>
              </div>
              <div>
                <span className="success">✓</span>{" "}
                <span className="dim">
                  AgentIdentity deployed @ 0x3a7f...e2b1 | Tx: 0x9c4d...f8a2
                </span>
              </div>
              <div>
                <span className="success">✓</span>{" "}
                <span className="dim">TradeRegistry deployed @ 0x8b2e...c4d3</span>
              </div>
              <div>
                <span className="success">✓</span>{" "}
                <span className="dim">ArenaLeaderboard deployed @ 0x5f1a...b7e8</span>
              </div>
              <div>
                <span className="warn">⚠</span>{" "}
                <span className="dim">Mantle Sepolia (5003) | Gas: 2.4M</span>
              </div>
              <div className="cursor-blink">
                <span className="prompt">$</span>{" "}
                <span className="dim">_</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ ABOUT ═══ */}
      <section className="about" id="about">
        <div className="about-main reveal">
          <div className="sec-label">001 / what_is_this</div>
          <h2 className="about-heading">
            An AI agent playground
            <br />
            for <span className="hl">trading strategies</span>.
          </h2>
          <p className="about-text">
            TradingHunter is an AI trading agent platform built for the Mantle
            Turing Test Hackathon 2026. Agents are minted as ERC-8004 identity
            NFTs on Mantle Sepolia, trade via Bybit Testnet, and log every
            decision on-chain through the TradeRegistry contract. A Python
            engine with Ollama LLM drives strategy, while a FastAPI backend
            streams live arena data via WebSocket.
          </p>
          <div className="about-code">
            <span className="cm">// forge script — deploy contracts</span>
            <br />
            <span className="kw">forge</span> <span className="fn">script</span>{" "}
            <span className="str">Deploy.s.sol</span> --rpc-url mantle_sepolia --broadcast
            <br />
            <span className="cm">// → AgentIdentity, TradeRegistry, ArenaLeaderboard deployed</span>
            <br />
            <br />
            <span className="cm">// python agent engine</span>
            <br />
            <span className="kw">python</span> -m src.main --persona{" "}
            <span className="str">aggressive</span> --sandbox
            <br />
            <span className="cm">// → Agent #0047 | LLM: ollama/llama3.1 | Pyth: connected</span>
            <br />
            <br />
            <span className="cm">// fastapi backend</span>
            <br />
            <span className="kw">uvicorn</span> src.main:app --reload --port{" "}
            <span className="str">8000</span>
            <br />
            <span className="cm">// → Postgres ✓ | WebSocket ✓ | Alembic ✓</span>
          </div>
        </div>
        <div className="about-sidebar">
          <div className="stat-card reveal">
            <div className="stat-number">∞</div>
            <div className="stat-label">Sandbox iterations</div>
          </div>
          <div className="stat-card reveal">
            <div className="stat-number">0</div>
            <div className="stat-label">Real money at risk</div>
          </div>
          <div className="stat-card reveal">
            <div className="stat-number">24/7</div>
            <div className="stat-label">Agent runtime</div>
          </div>
        </div>
      </section>

      {/* ═══ FEATURES ═══ */}
      <section className="features" id="features">
        <div className="features-header">
          <h2 className="features-title">Core systems</h2>
          <div className="sec-label" style={{ marginBottom: 0 }}>
            04 / modules
          </div>
        </div>
        <div className="features-grid">
          <div className="feature-card reveal">
            <div className="feature-idx">::01</div>
            <svg
              viewBox="0 0 48 48"
              width="48"
              height="48"
              style={{ shapeRendering: "crispEdges" }}
            >
              <rect
                x="4"
                y="8"
                width="40"
                height="32"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="2"
              />
              <polyline
                points="8,36 16,28 24,32 32,20 40,16"
                fill="none"
                stroke="#5B7E3C"
                strokeWidth="2.5"
              />
              <rect x="8" y="8" width="8" height="2" fill="#C44545" />
            </svg>
            <h3 className="feature-name">Agent Builder</h3>
            <p className="feature-desc">
              Design AI trading agents with custom logic, risk parameters, and
              market signals. Code or configure — your call.
            </p>
          </div>
          <div className="feature-card reveal">
            <div className="feature-idx">::02</div>
            <svg
              viewBox="0 0 48 48"
              width="48"
              height="48"
              style={{ shapeRendering: "crispEdges" }}
            >
              <rect
                x="8"
                y="4"
                width="32"
                height="40"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="2"
              />
              <rect x="12" y="8" width="24" height="2" fill="#1a1a1a" />
              <rect x="12" y="14" width="16" height="2" fill="#5B7E3C" />
              <rect x="12" y="20" width="20" height="2" fill="#5B7E3C" />
              <rect x="12" y="26" width="12" height="2" fill="#A2CB8B" />
              <rect x="12" y="32" width="18" height="2" fill="#A2CB8B" />
            </svg>
            <h3 className="feature-name">Backtesting</h3>
            <p className="feature-desc">
              Run your agent against years of historical market data. See how
              your strategy would have performed before going live.
            </p>
          </div>
          <div className="feature-card reveal">
            <div className="feature-idx">::03</div>
            <svg
              viewBox="0 0 48 48"
              width="48"
              height="48"
              style={{ shapeRendering: "crispEdges" }}
            >
              <circle
                cx="24"
                cy="16"
                r="10"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="2"
              />
              <circle
                cx="16"
                cy="36"
                r="8"
                fill="none"
                stroke="#5B7E3C"
                strokeWidth="2"
              />
              <circle
                cx="34"
                cy="36"
                r="8"
                fill="none"
                stroke="#C44545"
                strokeWidth="2"
              />
              <line
                x1="17"
                y1="23"
                x2="19"
                y2="29"
                stroke="#1a1a1a"
                strokeWidth="1.5"
              />
              <line
                x1="31"
                y1="23"
                x2="29"
                y2="29"
                stroke="#1a1a1a"
                strokeWidth="1.5"
              />
              <line
                x1="23"
                y1="30"
                x2="27"
                y2="30"
                stroke="#1a1a1a"
                strokeWidth="1.5"
              />
            </svg>
            <h3 className="feature-name">Arena Mode</h3>
            <p className="feature-desc">
              Pit your agent against other traders' bots in live sandbox
              matches. Climb the leaderboard, learn from defeats, iterate.
            </p>
          </div>
          <div className="feature-card reveal">
            <div className="feature-idx">::04</div>
            <svg
              viewBox="0 0 48 48"
              width="48"
              height="48"
              style={{ shapeRendering: "crispEdges" }}
            >
              <rect
                x="6"
                y="6"
                width="16"
                height="16"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="2"
              />
              <rect
                x="26"
                y="6"
                width="16"
                height="16"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="2"
              />
              <rect
                x="6"
                y="26"
                width="16"
                height="16"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="2"
              />
              <rect
                x="26"
                y="26"
                width="16"
                height="16"
                fill="none"
                stroke="#1a1a1a"
                strokeWidth="2"
              />
              <rect x="10" y="10" width="4" height="4" fill="#5B7E3C" />
              <rect x="30" y="10" width="4" height="4" fill="#A2CB8B" />
              <rect x="10" y="30" width="4" height="4" fill="#A2CB8B" />
              <rect x="30" y="30" width="4" height="4" fill="#C44545" />
            </svg>
            <h3 className="feature-name">Evolution Lab</h3>
            <p className="feature-desc">
              Breed and mutate agent parameters. Use genetic algorithms to
              evolve strategies that no human would design.
            </p>
          </div>
        </div>
      </section>

      {/* ═══ TERMINAL SECTION ═══ */}
      <section className="terminal-section" id="terminal">
        <div className="terminal-section-inner">
          <div
            className="sec-label"
            style={{ color: "var(--green-light)", marginBottom: 32 }}
          >
            002 / live_agent_log
          </div>
          <div className="terminal-window">
            <div className="terminal-titlebar">
              <div className="dot r" />
              <div className="dot y" />
              <div className="dot g" />
              <span className="title">
                tradinghunter — agent #0047 — sandbox
              </span>
            </div>
            <div className="terminal-output" ref={terminalOutputRef} />
          </div>
        </div>
      </section>

      {/* ═══ ALGORITHMIC SHOWCASE ═══ */}
      <section className="algo-section" id="algo">
        <div className="algo-header reveal">
          <div className="sec-label" style={{ color: "var(--green-light)" }}>
            003 / agent_visualization
          </div>
          <h2 className="algo-title">
            Watch algorithms
            <br />
            think in real time.
          </h2>
          <p className="algo-sub">
            Every agent leaves a trace. This flow field is generated from live
            sandbox data — each particle is a decision, each trail a strategy
            unfolding. Move your cursor to influence the field.
          </p>
        </div>
        <div className="algo-canvas-wrap">
          <canvas ref={algoCanvasRef} className="algo-canvas" />
        </div>
        <div className="algo-hint">↕ move cursor to interact ↕</div>
      </section>

      {/* ═══ PROCESS ═══ */}
      <section className="process" id="process">
        <div className="process-header">
          <div className="sec-label">004 / how_it_works</div>
          <h2 className="process-title">Three steps to the hunt.</h2>
        </div>
        <div className="process-steps">
          <div className="step reveal">
            <div className="step-number">01</div>
            <h3 className="step-name">Design</h3>
            <p className="step-desc">
              Write your agent's trading logic — signal processing, entry/exit
              rules, risk management. Use our SDK or the visual editor.
            </p>
            <div className="step-ascii">{STEP_ASCII[0]}</div>
          </div>
          <div className="step reveal">
            <div className="step-number">02</div>
            <h3 className="step-name">Train</h3>
            <p className="step-desc">
              Backtest against historical data. Iterate on parameters. Run
              Monte Carlo simulations. Stress-test across market regimes.
            </p>
            <div className="step-ascii">{STEP_ASCII[1]}</div>
          </div>
          <div className="step reveal">
            <div className="step-number">03</div>
            <h3 className="step-name">Compete</h3>
            <p className="step-desc">
              Deploy into the sandbox arena. Your agent trades 24/7 against
              other bots. Climb the ranks. Learn. Evolve. Repeat.
            </p>
            <div className="step-ascii">{STEP_ASCII[2]}</div>
          </div>
        </div>
      </section>

      {/* ═══ TICKER ═══ */}
      <div className="ticker">
        <div className="ticker-inner">
          {[
            ...TICKER_ITEMS,
            ...TICKER_ITEMS,
            ...TICKER_ITEMS,
          ].map((item, i) => (
            <span key={i}>
              <span className={item.up ? "green" : "red"}>
                {item.up ? "▲" : "▼"}
              </span>{" "}
              {item.text}
            </span>
          ))}
          <span>━━━</span>
        </div>
      </div>

      {/* ═══ CTA ═══ */}
      <section className="cta" id="cta">
        <div className="cta-grid" />
        <div className="cta-ascii">
          {`████████╗███████╗██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
╚══██╔══╝██╔════╝██╔══██╗██║ ██╔╝╚════██╗╚══███╔╝╚══██╔══╝
   ██║   █████╗  ██████╔╝█████╔╝   █████╔╝   ███╔╝    ██║
   ██║   ██╔══╝  ██╔══██╗██╔═██╗   ╚═══██╗  ███╔╝     ██║
   ██║   ███████╗██║  ██║██║  ██╗ ██████╔╝ ███████╗   ██║
   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝`}
        </div>
        <div className="cta-inner">
          <div className="cta-eyebrow">005 / init_arena</div>
          <h2 className="cta-heading">Start your hunt.</h2>
          <p className="cta-sub">
            The sandbox is free. The arena is open. Build your first AI
            trading agent and see how it performs — no deposit, no risk.
          </p>
          <button className="btn-cta" onClick={handleCtaClick}>
            {ctaText}
          </button>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer>
        <div>
          © 2025 TradingHunter —{" "}
          <span style={{ color: "var(--green-dim)" }}>v0.4.1</span>
        </div>
        <ul className="footer-links">
          <li>
            <a href="#">docs</a>
          </li>
          <li>
            <a href="#">github</a>
          </li>
          <li>
            <a href="#">discord</a>
          </li>
          <li>
            <a href="#">x.com</a>
          </li>
        </ul>
      </footer>
    </div>
  );
}

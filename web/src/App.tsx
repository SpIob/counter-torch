import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { Flame } from "./components/Flame";
import { Space } from "./components/Space";
import { Ask } from "./features/ask/Ask";
import { Compare } from "./features/compare/Compare";
import { CoverageMap } from "./features/coverage-map/CoverageMap";
import { Ranker } from "./features/ranker/Ranker";

const TABS = [
  { id: "coverage", label: "Coverage", C: CoverageMap },
  { id: "rank", label: "Ranker", C: Ranker },
  { id: "compare", label: "Compare", C: Compare },
  { id: "ask", label: "Ask", C: Ask },
] as const;

export default function App() {
  const [tab, setTab] = useState<string>(() => location.hash.slice(1) || "coverage");
  const refs = useRef<Record<string, HTMLButtonElement | null>>({});
  const [ind, setInd] = useState({ x: 0, w: 0 });
  const [go, setGo] = useState(false);

  useEffect(() => { location.hash = tab; }, [tab]);
  useLayoutEffect(() => {
    const place = () => { const el = refs.current[tab]; if (el) setInd({ x: el.offsetLeft, w: el.offsetWidth }); };
    place();
    const raf = requestAnimationFrame(() => setGo(true));
    window.addEventListener("resize", place);
    return () => { cancelAnimationFrame(raf); window.removeEventListener("resize", place); };
  }, [tab]);

  const Active = (TABS.find((t) => t.id === tab) ?? TABS[0]).C;
  return (
    <>
      <Space />
      <header className="top">
        <div className="wrap">
          <div className="brand"><Flame size={30} /><h1>Project Counter-Torch</h1></div>
          <nav className="tabs" role="tablist" aria-label="Views">
            <span className={`tab-ind ${go ? "go" : ""}`} style={{ width: ind.w, transform: `translateX(${ind.x}px)` }} aria-hidden="true" />
            {TABS.map((t) => (
              <button key={t.id} ref={(el) => { refs.current[t.id] = el; }} role="tab" aria-selected={tab === t.id} className="tab" onClick={() => setTab(t.id)}>{t.label}</button>
            ))}
          </nav>
        </div>
      </header>
      <main className="wrap"><div className="view" key={tab}><Active /></div></main>
      <footer className="wrap foot">Data from NASA Physical Sciences Informatics (psi.nasa.gov) and the Space Apps challenge brief.</footer>
    </>
  );
}

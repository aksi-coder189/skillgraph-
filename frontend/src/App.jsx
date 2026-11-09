import React, { useEffect, useState, useCallback } from "react";
import ReactFlow, { Background, Controls } from "reactflow";
import "reactflow/dist/style.css";

const BASE = import.meta.env.VITE_API || (import.meta.env.PROD ? "http://127.0.0.1:8000/api" : "/api");
let TOKEN = localStorage.getItem("sg_token") || "";
async function api(path, opts = {}) {
  const isForm = opts.body instanceof FormData;
  const r = await fetch(BASE + path, { ...opts, headers: { ...(isForm ? {} : { "Content-Type": "application/json" }), Authorization: "Bearer " + TOKEN },
    body: isForm ? opts.body : opts.body && JSON.stringify(opts.body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail || "Request failed");
  return j;
}
const Tag = ({ s }) => <span className={"tag " + s}>{s}</span>;

function Login({ onDone }) {
  const [f, setF] = useState({ email: "", password: "" }), [mode, setMode] = useState("login"), [err, setErr] = useState("");
  const go = async () => { try { const r = await api("/auth/" + mode, { method: "POST", body: f }); TOKEN = r.token; localStorage.setItem("sg_token", TOKEN); onDone(); } catch (e) { if (mode === "register" && /already registered/i.test(e.message)) { setMode("login"); setErr("This email already has an account. Sign in, or use a different email to create one."); } else { setErr(e.message); } } };
  return <main style={{ margin: "10vh auto", maxWidth: 380 }}><h1>SkillGraph</h1>
    <p className="mute">Know where you stand, what you're missing, and the shortest path to your target role.</p>
    <div className="panel" style={{ display: "grid", gap: ".7rem" }}>
      <input placeholder="Email" value={f.email} onChange={e => setF({ ...f, email: e.target.value })} />
      <input placeholder="Password" type="password" value={f.password} onChange={e => setF({ ...f, password: e.target.value })} />
      <button className="b" onClick={go}>{mode === "login" ? "Sign in" : "Create account"}</button>
      <button className="mute" style={{ background: "none", border: 0, cursor: "pointer" }} onClick={() => setMode(mode === "login" ? "register" : "login")}>
        {mode === "login" ? "New here? Create an account" : "Have an account? Sign in"}</button>
      {err && <div className="err">{err}</div>}</div></main>;
}

function Dashboard({ role }) {
  const [a, setA] = useState(null);
  useEffect(() => { api("/analysis?role=" + encodeURIComponent(role)).then(setA); }, [role]);
  if (!a) return null;
  const crit = a.gaps.filter(g => g.status === "missing").length, mid = a.gaps.filter(g => g.status === "partial").length, ok = a.gaps.filter(g => g.status === "strong").length;
  return <>
    <div className="panel row"><div><h2 style={{ fontSize: "3rem", margin: 0 }}>{a.readiness}%</h2><span className="mute">ready for {role}</span></div>
      <div className="row"><Tag s="missing" /> {crit} critical <Tag s="partial" /> {mid} partial <Tag s="strong" /> {ok} strong</div></div>
    <div className="panel"><h3>Skill gaps, ranked by priority</h3>
      <table><thead><tr><th>Skill</th><th>Status</th><th>Mastery</th><th>Confidence</th><th>Unlocks</th><th>Priority</th></tr></thead><tbody>
        {a.gaps.map(g => <tr key={g.skill}><td>{g.skill}</td><td><Tag s={g.status} /></td>
          <td><div className="bar"><i style={{ width: Math.min(100, g.eff / .75 * 100) + "%" }} /></div></td>
          <td>{Math.round(g.confidence * 100)}%</td><td>{g.downstream}</td><td>{g.priority}</td></tr>)}</tbody></table>
      <p className="mute">Priority = importance × gap × market demand × downstream impact.</p></div>
    <div className="panel"><h3>Realistic career paths from where you are</h3>
      <table><tbody>{a.paths.map(p => <tr key={p.role}><td>{p.role}</td>
        <td><div className="bar"><i style={{ width: p.readiness + "%" }} /></div></td><td>{p.readiness}%</td>
        <td className="mute">{p.missing} missing, {p.partial} partial</td></tr>)}</tbody></table></div></>;
}

function Skills({ meta, reload }) {
  const [p, setP] = useState(null), [name, setName] = useState(""), [msg, setMsg] = useState("");
  const load = () => api("/profile").then(setP); useEffect(() => { load(); }, []);
  if (!p) return null;
  const set = (s, k, v) => setP({ ...p, skills: { ...p.skills, [s]: { ...p.skills[s], [k]: v } } });
  const add = () => { if (name) { setP({ ...p, skills: { ...p.skills, [name]: { level: 2, projects: 0, certs: 0, github: false, assessment: null } } }); setName(""); } };
  const save = async () => { const r = await api("/profile", { method: "PUT", body: { skills: p.skills, target: p.target } }); setP(r); setMsg("Saved"); reload(); };
  const up = async e => { const fd = new FormData(); fd.append("file", e.target.files[0]); const r = await api("/resume", { method: "POST", body: fd }); setP(r); setMsg(`Found ${r.found.length} skills in your resume`); reload(); };
  return <>
    <div className="panel row"><label>Upload resume (PDF or text) <input type="file" accept=".pdf,.txt" onChange={up} /></label>
      <input list="sk" placeholder="Add skill manually" value={name} onChange={e => setName(e.target.value)} />
      <datalist id="sk">{meta.skills.map(s => <option key={s} value={s} />)}</datalist>
      <button className="b" onClick={add}>Add</button><button className="b" onClick={save}>Save changes</button><span className="mute">{msg}</span></div>
    <div className="panel"><h3>Your skills and the evidence behind them</h3>
      <table><thead><tr><th>Skill</th><th>Claimed level</th><th>Projects</th><th>Certs</th><th>GitHub</th><th>Test %</th><th>Confidence</th></tr></thead><tbody>
        {Object.entries(p.skills).map(([s, e]) => <tr key={s}><td>{s}</td>
          <td><select value={e.level} onChange={x => set(s, "level", +x.target.value)}>{["Beginner", "Intermediate", "Advanced", "Expert"].map((l, i) => <option key={l} value={i + 1}>{l}</option>)}</select></td>
          <td><input type="number" min="0" style={{ width: 60 }} value={e.projects} onChange={x => set(s, "projects", +x.target.value)} /></td>
          <td><input type="number" min="0" style={{ width: 60 }} value={e.certs} onChange={x => set(s, "certs", +x.target.value)} /></td>
          <td><input type="checkbox" checked={e.github} onChange={x => set(s, "github", x.target.checked)} /></td>
          <td><input type="number" min="0" max="100" style={{ width: 70 }} value={e.assessment ?? ""} onChange={x => set(s, "assessment", x.target.value === "" ? null : +x.target.value)} /></td>
          <td>{p.computed[s] ? Math.round(p.computed[s].confidence * 100) + "%" : "save to compute"}</td></tr>)}</tbody></table>
      {!Object.keys(p.skills).length && <p className="mute">No skills yet. Upload a resume or add a skill above.</p>}</div></>;
}

const COL = { strong: "#5fd4a0", partial: "#f2c14e", missing: "#ff6b6b", role: "#4cc9f0" };
function Graph({ role }) {
  const [g, setG] = useState(null);
  useEffect(() => { api("/graph?role=" + encodeURIComponent(role)).then(setG); }, [role]);
  if (!g) return null;
  const idx = {}, nodes = g.nodes.map(n => { const i = idx[n.layer] = (idx[n.layer] ?? -1) + 1;
    return { id: n.id, position: { x: n.layer * 230, y: i * 70 }, data: { label: n.id },
      style: { background: "#142830", color: "#e8f1f2", border: `2px solid ${COL[n.status]}`, borderRadius: 8, width: 160, fontSize: 13 } }; });
  const edges = g.edges.map(e => ({ id: e.from + e.to, source: e.from, target: e.to, animated: e.to === role, style: { stroke: "#4a6b75" } }));
  return <div className="panel"><h3>Skill graph for {role}</h3><p className="mute">Border colour shows your status: green strong, yellow partial, red missing. Arrows point from prerequisite to skill to role.</p>
    <div style={{ height: 560 }}><ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable><Background color="#24414b" /><Controls /></ReactFlow></div></div>;
}

function Roadmap({ role }) {
  const [r, setR] = useState(null);
  useEffect(() => { api("/roadmap?role=" + encodeURIComponent(role)).then(setR); }, [role]);
  if (!r) return null;
  return <>{!r.phases.length && <div className="panel">No gaps found. You cover this role's skills.</div>}
    {r.phases.map(ph => <div className="panel" key={ph.name}><h3>{ph.name}</h3>
      <div className="row">{ph.skills.map(s => <span key={s.skill} className={"tag " + s.status}>{s.skill}</span>)}</div></div>)}
    {!!r.projects.length && <div className="panel"><h3>Build these to prove the skills</h3>
      {r.projects.map(p => <p key={p.title}><b>{p.title}</b>: {p.desc}.<br /><span className="mute">Proves: {p.skills.join(", ")}</span></p>)}</div>}</>;
}

function Simulator({ role }) {
  const [a, setA] = useState(null), [pick, setPick] = useState([]), [res, setRes] = useState(null);
  useEffect(() => { api("/analysis?role=" + encodeURIComponent(role)).then(setA); setPick([]); setRes(null); }, [role]);
  useEffect(() => { api("/simulate", { method: "POST", body: { role, learn: pick } }).then(setRes); }, [pick, role]);
  if (!a) return null;
  const toggle = s => setPick(pick.includes(s) ? pick.filter(x => x !== s) : [...pick, s]);
  return <div className="panel"><h3>What if I learn…?</h3>
    <div className="row">{a.gaps.filter(g => g.status !== "strong").map(g => <label key={g.skill}>
      <input type="checkbox" checked={pick.includes(g.skill)} onChange={() => toggle(g.skill)} /> {g.skill}</label>)}</div>
    {res && <><h2 style={{ marginTop: "1rem" }}>{res.before}% → {res.after}%</h2>
      <p className="mute">Readiness if each skill alone were learned:</p>
      <table><tbody>{Object.entries(res.each).map(([s, v]) => <tr key={s}><td>{s}</td><td>{v}%</td><td className="mute">+{(v - res.before).toFixed(1)}</td></tr>)}</tbody></table></>}</div>;
}

function Assistant({ role }) {
  const [q, setQ] = useState(""), [a, setA] = useState(""), [busy, setBusy] = useState(false);
  const ask = async () => { setBusy(true); try { setA((await api("/assistant", { method: "POST", body: { role, question: q || null } })).answer); } finally { setBusy(false); } };
  return <div className="panel"><h3>Career assistant</h3>
    <div className="row"><input style={{ flex: 1 }} placeholder="Why should I learn Docker first? (leave empty for a full explanation)" value={q} onChange={e => setQ(e.target.value)} />
      <button className="b" onClick={ask} disabled={busy}>{busy ? "Thinking…" : "Ask"}</button></div>
    {a && <div className="chat">{a}</div>}</div>;
}

export default function App() {
  const [authed, setAuthed] = useState(!!TOKEN), [meta, setMeta] = useState(null), [tab, setTab] = useState("Dashboard"), [role, setRole] = useState(""), [k, setK] = useState(0);
  const init = useCallback(async () => { try { const m = await api("/meta"); const p = await api("/profile"); setMeta(m); setRole(p.target); setAuthed(true); } catch { TOKEN = ""; localStorage.removeItem("sg_token"); setAuthed(false); } }, []);
  useEffect(() => { if (TOKEN) init(); }, [init]);
  if (!authed || !meta) return <Login onDone={init} />;
  const tabs = ["Dashboard", "Skills", "Graph", "Roadmap", "Simulator", "Assistant"];
  const view = { Dashboard: <Dashboard role={role} key={k} />, Skills: <Skills meta={meta} reload={() => setK(k + 1)} />, Graph: <Graph role={role} key={k} />,
    Roadmap: <Roadmap role={role} key={k} />, Simulator: <Simulator role={role} key={k} />, Assistant: <Assistant role={role} /> }[tab];
  return <div className="app"><nav><h1>SkillGraph</h1>{tabs.map(t => <button key={t} className={t === tab ? "on" : ""} onClick={() => setTab(t)}>{t}</button>)}
    <button onClick={() => { localStorage.removeItem("sg_token"); TOKEN = ""; setAuthed(false); }}>Sign out</button></nav>
    <main><div className="row" style={{ marginBottom: "1rem" }}><h2 style={{ margin: 0 }}>{tab}</h2><span className="mute">Target role</span>
      <select value={role} onChange={async e => { setRole(e.target.value); const p = await api("/profile"); api("/profile", { method: "PUT", body: { skills: p.skills, target: e.target.value } }); }}>
        {meta.roles.map(r => <option key={r}>{r}</option>)}</select></div>{view}</main></div>;
}

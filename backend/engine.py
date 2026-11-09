"""SkillGraph core engine: normalization, extraction, evidence confidence,
dependency-aware gap priority, what-if simulation, roadmap, projects, LLM."""
import os, re
from difflib import get_close_matches

# skill: (category, market_demand, prerequisites)
SKILLS = {
 "Python":("Programming",.95,[]), "SQL":("Data",.9,[]), "Git":("Tools",.85,[]),
 "Statistics":("Math",.8,[]), "NumPy":("Data",.8,["Python"]), "Pandas":("Data",.85,["Python"]),
 "Machine Learning":("ML",.9,["Python","Statistics","NumPy","Pandas"]),
 "Deep Learning":("ML",.85,["Machine Learning"]), "PyTorch":("ML",.85,["Deep Learning"]),
 "Docker":("DevOps",.85,["Git"]), "FastAPI":("Backend",.7,["Python"]),
 "MLOps":("DevOps",.75,["Docker","Machine Learning"]), "Cloud":("Cloud",.85,["Docker"]),
 "System Design":("Engineering",.7,[]), "Excel":("Data",.8,[]),
 "Power BI":("Data",.75,["Excel","SQL"]), "Data Visualization":("Data",.7,["Pandas"]),
 "JavaScript":("Frontend",.9,[]), "React":("Frontend",.85,["JavaScript"]),
 "HTML/CSS":("Frontend",.8,[]), "Node.js":("Backend",.75,["JavaScript"]),
 "REST APIs":("Backend",.8,[]), "PostgreSQL":("Data",.75,["SQL"]),
 "CI/CD":("DevOps",.7,["Git","Docker"]),
}
ROLES = {
 "Machine Learning Engineer":{"Python":.95,"PyTorch":.9,"Machine Learning":.95,"Deep Learning":.85,"Docker":.75,"MLOps":.75,"FastAPI":.6,"Cloud":.6,"System Design":.5,"SQL":.6,"Git":.6},
 "Data Scientist":{"Python":.95,"Statistics":.9,"Pandas":.9,"NumPy":.8,"Machine Learning":.9,"SQL":.8,"Data Visualization":.7,"Deep Learning":.5},
 "Data Analyst":{"SQL":.95,"Excel":.85,"Power BI":.8,"Python":.6,"Pandas":.6,"Statistics":.6,"Data Visualization":.8},
 "Full Stack Developer":{"JavaScript":.95,"React":.9,"HTML/CSS":.85,"Node.js":.8,"REST APIs":.8,"PostgreSQL":.7,"Git":.7,"Docker":.5,"CI/CD":.4},
 "Backend Developer":{"Python":.8,"FastAPI":.7,"REST APIs":.9,"PostgreSQL":.8,"Docker":.7,"System Design":.7,"Git":.7,"Cloud":.6,"CI/CD":.5},
}
PROJECTS = [
 ("Containerized ML API","Serve a trained model with FastAPI inside Docker",["Docker","FastAPI","REST APIs","MLOps"]),
 ("End-to-end ML Pipeline with CI/CD","Train, track and auto-deploy a model on every push",["MLOps","CI/CD","Git","Machine Learning"]),
 ("PyTorch Image Classifier","CNN trained from scratch with evaluation report",["PyTorch","Deep Learning","Machine Learning"]),
 ("Sales Analytics Dashboard","Clean data in SQL/Pandas and build an interactive dashboard",["SQL","Pandas","Data Visualization","Power BI","Excel"]),
 ("Full-stack Task Manager","React UI + Node REST API + PostgreSQL",["React","Node.js","REST APIs","PostgreSQL","JavaScript","HTML/CSS"]),
 ("Cloud-deployed Service","Deploy an API on AWS/GCP with monitoring",["Cloud","Docker","System Design","FastAPI"]),
 ("Statistical Study with Visuals","Hypothesis tests and EDA on a public dataset",["Statistics","Pandas","NumPy","Data Visualization"]),
]
ALIASES = {"py":"Python","sklearn":"Machine Learning","scikit-learn":"Machine Learning","ml":"Machine Learning",
 "dl":"Deep Learning","tensorflow":"Deep Learning","keras":"Deep Learning","torch":"PyTorch","js":"JavaScript",
 "reactjs":"React","react.js":"React","nodejs":"Node.js","node":"Node.js","postgres":"PostgreSQL","powerbi":"Power BI",
 "aws":"Cloud","gcp":"Cloud","azure":"Cloud","rest":"REST APIs","rest api":"REST APIs","html":"HTML/CSS","css":"HTML/CSS",
 "cicd":"CI/CD","github actions":"CI/CD","numpy":"NumPy","pandas":"Pandas","matplotlib":"Data Visualization",
 "seaborn":"Data Visualization","tableau":"Data Visualization","mlflow":"MLOps","kubernetes":"Docker","fastapi":"FastAPI"}
VOCAB = {**{s.lower():s for s in SKILLS}, **ALIASES}

def normalize(raw):
    k = raw.strip().lower()
    if k in VOCAB: return VOCAB[k]
    m = get_close_matches(k, list(VOCAB), n=1, cutoff=0.82)
    return VOCAB[m[0]] if m else None

def extract_skills(text):
    text = text.lower(); found = {}
    for key, canon in VOCAB.items():
        n = len(re.findall(r"(?<![\w+#.])" + re.escape(key) + r"(?![\w+#])", text))
        if n: found[canon] = found.get(canon, 0) + n
    return {s: {"level": 3 if n >= 3 else 2, "projects": 0, "certs": 0, "github": False, "assessment": None}
            for s, n in found.items()}

def confidence(e):
    c = .25 + .12*min(e.get("projects",0),4) + .1*min(e.get("certs",0),2) + (.1 if e.get("github") else 0)
    if e.get("assessment") is not None: c += .3*e["assessment"]/100
    return round(min(c, .99), 2)

def effective(e):
    claim = e.get("level",1)/4
    if e.get("assessment") is not None: claim = .4*claim + .6*e["assessment"]/100
    return round(min(claim*(.6+.4*confidence(e)), 1), 3)

def _downstream(skill, pool):
    return sum(1 for o in pool if o != skill and skill in _closure(o))

def _closure(s, seen=None):
    seen = seen if seen is not None else set()
    for p in SKILLS[s][2]:
        if p not in seen: seen.add(p); _closure(p, seen)
    return seen

def analyze(profile, role, override=None):
    override = override or {}; sk = profile.get("skills", {}); req = ROLES[role]; rows = []
    effs = {s: override.get(s, effective(sk[s]) if s in sk else 0) for s in req}
    gaps = [s for s in req if effs[s] < .4]
    for s, imp in req.items():
        eff = effs[s]; gap = round(max(0, 1-eff/.75), 3)
        down = _downstream(s, gaps)
        prio = round(imp*gap*SKILLS[s][1]*(1+.25*down), 3)
        status = "strong" if eff >= .55 else "partial" if eff >= .25 else "missing"
        rows.append({"skill":s,"importance":imp,"eff":eff,"gap":gap,"status":status,"demand":SKILLS[s][1],
                     "downstream":down,"priority":prio,"confidence":confidence(sk[s]) if s in sk else 0,
                     "category":SKILLS[s][0]})
    readiness = round(100*sum(r["importance"]*min(r["eff"]/.75,1) for r in rows)/sum(req.values()), 1)
    rows.sort(key=lambda r: -r["priority"])
    return {"role":role,"readiness":readiness,"gaps":rows}

def simulate(profile, role, learn):
    base = analyze(profile, role)["readiness"]
    after = analyze(profile, role, {s: max(.8, effective(profile["skills"][s]) if s in profile.get("skills",{}) else 0) for s in learn})["readiness"]
    singles = {s: analyze(profile, role, {s: .8})["readiness"] for s in ROLES[role]
               if analyze(profile, role)["gaps"] and next(r for r in analyze(profile, role)["gaps"] if r["skill"]==s)["status"] != "strong"}
    return {"before":base,"after":after,"each":dict(sorted(singles.items(), key=lambda x:-x[1]))}

def paths(profile):
    out = []
    for r in ROLES:
        a = analyze(profile, r)
        out.append({"role":r,"readiness":a["readiness"],"missing":sum(g["status"]=="missing" for g in a["gaps"]),
                    "partial":sum(g["status"]=="partial" for g in a["gaps"])})
    return sorted(out, key=lambda x: -x["readiness"])

def roadmap(profile, role):
    a = analyze(profile, role); todo = {g["skill"]:g for g in a["gaps"] if g["status"] != "strong"}
    depth = {}
    def d(s):
        if s not in depth: depth[s] = 0 if not [p for p in SKILLS[s][2] if p in todo] else 1+max(d(p) for p in SKILLS[s][2] if p in todo)
        return depth[s]
    for s in todo: d(s)
    names = ["Foundations","Core skills","Engineering","Advanced"]; phases = {}
    for s in sorted(todo, key=lambda x:(depth[x], -todo[x]["priority"])):
        phases.setdefault(min(depth[s],3), []).append(todo[s])
    projs = sorted(PROJECTS, key=lambda p: -sum(todo[s]["priority"] for s in p[2] if s in todo))
    return {"role":role,"phases":[{"name":names[i],"skills":phases[i]} for i in sorted(phases)],
            "projects":[{"title":p[0],"desc":p[1],"skills":[s for s in p[2] if s in todo]} for p in projs[:3] if any(s in todo for s in p[2])]}

def graph(profile, role):
    a = {g["skill"]:g for g in analyze(profile, role)["gaps"]}; nodes = set(a)
    for s in list(a): nodes |= _closure(s)
    layer = {}
    def L(s):
        if s not in layer: layer[s] = 0 if not [p for p in SKILLS[s][2] if p in nodes] else 1+max(L(p) for p in SKILLS[s][2] if p in nodes)
        return layer[s]
    for s in nodes: L(s)
    sk = profile.get("skills", {})
    out = [{"id":s,"layer":layer[s],"status":a[s]["status"] if s in a else ("strong" if s in sk and effective(sk[s])>=.55 else "partial" if s in sk else "missing"),"core":s in a} for s in nodes]
    edges = [{"from":p,"to":s} for s in nodes for p in SKILLS[s][2] if p in nodes]
    top = max(layer.values())+1
    out.append({"id":role,"layer":top,"status":"role","core":True})
    edges += [{"from":s,"to":role} for s in a]
    return {"nodes":out,"edges":edges}

def llm(system, prompt, fallback):
    if not os.getenv("ANTHROPIC_API_KEY"): return fallback
    try:
        import anthropic
        r = anthropic.Anthropic().messages.create(model=os.getenv("CLAUDE_MODEL","claude-sonnet-4-6"),
            max_tokens=700, system=system, messages=[{"role":"user","content":prompt}])
        return r.content[0].text
    except Exception as e:
        return fallback + f"\n\n(LLM unavailable: {e})"

def explain(profile, role, question=None):
    a = analyze(profile, role); top = a["gaps"][:4]
    ctx = f"Target: {role}. Readiness {a['readiness']}%. Top priority gaps: " + "; ".join(
        f"{g['skill']} (priority {g['priority']}, unlocks {g['downstream']} other gaps, status {g['status']})" for g in top)
    fb = f"You are {a['readiness']}% ready for {role}. Start with {top[0]['skill']}: it has the highest priority score" + (
        f" and unlocks {top[0]['downstream']} other gaps." if top[0]["downstream"] else ".") if top else "You already cover this role's skills."
    sys = "You are SkillGraph's career coach. Use ONLY the computed analysis given. Be concise, concrete, and actionable."
    return llm(sys, f"{ctx}\n\nUser question: {question or 'Explain my gaps and what to do first.'}", fb)

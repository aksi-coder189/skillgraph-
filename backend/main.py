import os, io, json, time, hashlib, secrets
import pymysql
import jwt
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import engine as E

SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
DBN = os.getenv("DB_NAME", "skillgraph")
_cfg = dict(host=os.getenv("DB_HOST","127.0.0.1"), user=os.getenv("DB_USER","root"), password=os.getenv("DB_PASS",""), port=int(os.getenv("DB_PORT","3306")), autocommit=True)
_c = pymysql.connect(**_cfg); _c.cursor().execute(f"create database if not exists {DBN} character set utf8mb4"); _c.close()
db = pymysql.connect(database=DBN, **_cfg)
def q(sql, a=()):
    db.ping(reconnect=True); c = db.cursor(); c.execute(sql, a); return c
q("create table if not exists sg_users(id int auto_increment primary key, email varchar(190) unique, pw varchar(100), salt varchar(32), profile longtext)")
app = FastAPI(title="SkillGraph")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def h(pw, salt): return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 100_000).hex()
class Auth(BaseModel): email: str; password: str
class Profile(BaseModel): skills: dict = {}; target: str = "Machine Learning Engineer"
class Sim(BaseModel): role: str; learn: list[str]
class Ask(BaseModel): role: str; question: str | None = None

def user(authorization: str = Header(None)):
    try: uid = jwt.decode((authorization or "").replace("Bearer ", ""), SECRET, algorithms=["HS256"])["uid"]
    except Exception: raise HTTPException(401, "Invalid or expired token")
    return uid
def load(uid): return json.loads(q("select profile from sg_users where id=%s", (uid,)).fetchone()[0])
def save(uid, p): q("update sg_users set profile=%s where id=%s", (json.dumps(p), uid))
def token(uid): return jwt.encode({"uid": uid, "exp": time.time()+86400*7}, SECRET, algorithm="HS256")

@app.post("/api/auth/register")
def register(a: Auth):
    salt = secrets.token_hex(8)
    try: c = q("insert into sg_users(email,pw,salt,profile) values(%s,%s,%s,%s)", (a.email.lower(), h(a.password, salt), salt, json.dumps({"skills":{}, "target":"Machine Learning Engineer"})))
    except pymysql.err.IntegrityError: raise HTTPException(409, "Email already registered")
    return {"token": token(c.lastrowid)}

@app.post("/api/auth/login")
def login(a: Auth):
    r = q("select id,pw,salt from sg_users where email=%s", (a.email.lower(),)).fetchone()
    if not r or h(a.password, r[2]) != r[1]: raise HTTPException(401, "Wrong email or password")
    return {"token": token(r[0])}

@app.get("/api/meta")
def meta(): return {"roles": list(E.ROLES), "skills": list(E.SKILLS)}

@app.get("/api/profile")
def get_profile(uid=Depends(user)):
    p = load(uid)
    p["computed"] = {s: {"confidence": E.confidence(e), "effective": E.effective(e)} for s, e in p["skills"].items()}
    return p

@app.put("/api/profile")
def put_profile(p: Profile, uid=Depends(user)):
    clean = {}
    for s, e in p.skills.items():
        n = E.normalize(s)
        if n: clean[n] = {"level": int(e.get("level",1)), "projects": int(e.get("projects",0)), "certs": int(e.get("certs",0)),
                          "github": bool(e.get("github")), "assessment": e.get("assessment")}
    save(uid, {"skills": clean, "target": p.target}); return get_profile(uid)

@app.post("/api/resume")
async def resume(file: UploadFile = File(...), uid=Depends(user)):
    raw = await file.read()
    if file.filename.lower().endswith(".pdf"):
        from pypdf import PdfReader
        text = " ".join((pg.extract_text() or "") for pg in PdfReader(io.BytesIO(raw)).pages)
    else: text = raw.decode("utf-8", "ignore")
    found = E.extract_skills(text); p = load(uid)
    for s, e in found.items(): p["skills"].setdefault(s, e)
    save(uid, p); return {"found": list(found), **get_profile(uid)}

@app.get("/api/analysis")
def analysis(role: str, uid=Depends(user)):
    return {**E.analyze(load(uid), role), "paths": E.paths(load(uid))}
@app.post("/api/simulate")
def sim(s: Sim, uid=Depends(user)): return E.simulate(load(uid), s.role, s.learn)
@app.get("/api/roadmap")
def road(role: str, uid=Depends(user)): return E.roadmap(load(uid), role)
@app.get("/api/graph")
def graph(role: str, uid=Depends(user)): return E.graph(load(uid), role)
@app.post("/api/assistant")
def assistant(a: Ask, uid=Depends(user)): return {"answer": E.explain(load(uid), a.role, a.question)}

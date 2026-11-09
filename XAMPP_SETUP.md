# SkillGraph on XAMPP (Windows)

Apache + PHP cannot run Python, so: XAMPP = MySQL + Apache (frontend). Python backend runs separately.

## One-time setup
1. Install Python 3.10+ (tick "Add to PATH") and Node.js 18+.
2. Open XAMPP Control Panel -> Start **MySQL** and **Apache**.
   (Database "skillgraph" and the table are created automatically; view it at http://localhost/phpmyadmin)
3. Build the frontend:
       cd skillgraph\frontend
       npm install
       npm run build
4. Copy the generated `frontend\dist` folder contents into `C:\xampp\htdocs\skillgraph\`

## Every time you run it
1. Start MySQL + Apache in XAMPP.
2. Double-click `backend\start_backend.bat` (first run installs packages). Keep the window open.
   Check: http://127.0.0.1:8000/docs
3. Open http://localhost/skillgraph/

## Optional
- AI assistant with Claude: remove `rem` in start_backend.bat and put your key.
- If MySQL root has a password or a different port: set DB_PASS / DB_PORT env vars in the .bat (e.g. `set DB_PASS=yourpass`).
- Dev mode without Apache: `cd frontend && npm run dev` -> http://localhost:5173

## Troubleshooting
- "Can't connect to MySQL": MySQL not started in XAMPP, or port is not 3306 (set DB_PORT).
- Login works but pages fail: backend window not running, or port 8000 busy.
- Blank page in htdocs: copy the *contents* of dist, not the dist folder itself.

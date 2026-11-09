# SkillGraph XAMPP PHP/MySQL edition

This package runs the frontend and API with XAMPP Apache + PHP and stores data in XAMPP MySQL/MariaDB. It does not need VS Code, Python, or Node.js at runtime.

## Setup and run

1. Extract the XAMPP bundle. Start **Apache** and **MySQL** in XAMPP Control Panel.
2. Double-click `start-skillgraph.bat`. It copies the application to `htdocs/skillgraph` and opens `api/config.php` in Notepad the first time.
3. Configure the DB connection and replace `jwt_secret` with a unique random string of at least 32 characters. Save and close Notepad.
4. Double-click the launcher again. It creates the database, schema, and seed catalog, then opens `http://localhost/skillgraph/`.

The frontend and PHP API both run through Apache. The API is `/skillgraph/api/*`; all persistent app data is in MySQL/MariaDB. The original FastAPI backend remains in the source tree but is not included or used by this PHP bundle.

## Server requirements

- XAMPP with PHP 8.1 or newer, MySQL/MariaDB, `pdo_mysql`, `json`, `mbstring`, `curl` (optional LLM), and `zip` extensions.
- Apache `mod_rewrite` and `AllowOverride All` on the `htdocs` directory.
- `upload_max_filesize=6M` and `post_max_size=7M` in XAMPP `php.ini` for the 5 MB resume limit. Restart Apache after changing `php.ini`.

## Optional AI provider

The PHP API works without an LLM key and labels deterministic results `rule_based`. To enable structured extraction, skill normalization, and personalized explanations, set `ai_provider`, `ai_api_key`, `ai_base_url`, and `ai_model` in the server-side `api/config.php`. The secret is not returned to the browser. Provider/network/JSON validation failures fall back to deterministic behavior. This provider path needs the PHP cURL extension.

## Resume handling

Uploads are limited to 5 MB and parsed from PHP temporary storage; resume text is not saved in MySQL. DOCX parsing uses ZipArchive. Text-based PDF parsing supports common uncompressed literal-string text operators; scanned PDFs and some compressed/encoded PDF text are unsupported. Results are suggestions, not verified proficiency.

Keep `api/config.php` private. Apache rules block direct access to config, schema, and setup files. Use this package locally only; do not expose XAMPP to the public internet.

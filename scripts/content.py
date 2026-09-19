"""Profile content. Everything the SVGs say lives here; edit this file and run
`python scripts/build.py` to regenerate the assets."""

LOGIN = "Ahmed1-Rebai"
NAME = "Ahmed Rebai"
ROLE = "AI Automation & RAG Systems Engineer"
TAGLINE = "Evidence-grounded AI, real-time data pipelines, and the CI/CD that ships them."
EMAIL = "rebaiahmed244@gmail.com"
LINKEDIN = "linkedin.com/in/ahmed-rebai-18506938a"

FACTS = [
    ("BASED IN", "Sfax, Tunisia"),
    ("STUDYING", "Data Engineering, FSS · 2028"),
    ("FOCUS", "RAG · agents · streaming data"),
    ("CERTIFIED", "DP-700 · DP-600 · DP-900"),
]

TILES = [
    ("3", "Microsoft certifications", "DP-900 · DP-600 · DP-700"),
    ("3", "engineering internships", "2026 · AI, data and edge"),
    ("421", "automated tests shipped", "multi-agent AI platform"),
    ("0", "hallucinated citations", "enforced by a CI gate"),
]

EXPERIENCE = [
    {
        "role": "Software & Edge AI Engineer",
        "org": "CompiTechnology",
        "when": "AUG 2026",
        "where": "HYBRID",
        "bullets": [
            "Integrated a **TinyML model** (Edge Impulse, TFLite Micro) into a Wear OS app via C++/NDK/JNI and "
            "ported it to an Arduino nRF52, optimizing inference to **~2.5 s on constrained hardware**.",
            "Designed a **custom BLE/iBeacon protocol** and state machine; wrote low-power firmware for "
            "ESP32-C6/XIAO (light sleep) and an Arduino variant.",
            "Built a **Laravel 12 REST API** on SQLite (tracking, violations, sessions, inactivity logic) with "
            "PHPUnit tests, containerized with Docker.",
            "Shipped a **real-time React 18 + Inertia dashboard** (live stats, analytics, theming) fed by polling "
            "and WebSockets.",
        ],
        "learned": "Full-cycle delivery from embedded edge to data backend, and agreeing one protocol "
                   "across three codebases.",
        "chips": ["edgeimpulse", "TFLite Micro", "cplusplus", "arduino", "espressif", "laravel", "react", "docker"],
    },
    {
        "role": "AI Automation Engineering Intern",
        "org": "Novagate Solutions",
        "when": "JUN — JUL 2026",
        "where": "REMOTE",
        "bullets": [
            "Built the **automation and RAG core** of a multi-service platform (Next.js, FastAPI, Express, "
            "PostgreSQL), grounding LLM output in a **knowledge-graph memory layer** and real-time web search.",
            "Implemented **provider-agnostic LLM routing** with retry-with-backoff, plus auth, billing and "
            "DNS-automation integrations across a shared-database, multi-tenant architecture.",
            "Closed real security gaps before delivery: **broken workspace authorization** and "
            "**webhook forgery** on an unsigned third-party callback.",
        ],
        "chips": ["nextdotjs", "fastapi", "express", "postgresql", "RAG", "LLM routing"],
    },
    {
        "role": "AI Systems Engineering Intern",
        "org": "DESLAB",
        "when": "JUL 2026",
        "where": "ON-SITE",
        "bullets": [
            "Contributed to a **multi-agent AI system** (Flask, Vue 3, PostgreSQL, Redis/RQ) that writes "
            "evidence-grounded reports by orchestrating LLM agents through a **hand-built ReACT loop**, no LangChain.",
            "Built retrieval over a **temporal knowledge graph + live web search** so every generated claim "
            "traces to a real source, plus a mathematically computed **consensus score**.",
            "Backed it with a **421-test suite** (real Postgres/Redis integration tests) and a containerized "
            "GitLab CI/CD pipeline: lint → build → test → deploy.",
        ],
        "chips": ["flask", "vuedotjs", "postgresql", "redis", "docker", "gitlab"],
    },
    {
        "role": "Software Engineering Intern · ASP.NET Core",
        "org": "Engineering & Consulting “E&C”",
        "when": "AUG 2025",
        "where": "HYBRID",
        "bullets": [
            "Developed **Nova Write**, a blog/CMS platform on **ASP.NET Core MVC 8** with EF Core and "
            "SQL Server: CRUD, a relational schema and role-based access control.",
        ],
        "chips": ["dotnet", "EF Core", "SQL Server"],
    },
]

CERTS = [
    {
        "code": "DP-700",
        "name": ["Fabric Data Engineer"],
        "level": "ASSOCIATE",
        "date": "Sep 7, 2026",
        "url": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-data-engineer-associate/",
        "exam": "Implementing Data Engineering Solutions Using Microsoft Fabric",
    },
    {
        "code": "DP-600",
        "name": ["Fabric Analytics Engineer"],
        "level": "ASSOCIATE",
        "date": "Aug 28, 2026",
        "url": "https://learn.microsoft.com/en-us/credentials/certifications/fabric-analytics-engineer-associate/",
        "exam": "Implementing Analytics Solutions Using Microsoft Fabric",
    },
    {
        "code": "DP-900",
        "name": ["Azure Data Fundamentals"],
        "level": "FUNDAMENTALS",
        "date": "Aug 1, 2026",
        "url": "https://learn.microsoft.com/en-us/credentials/certifications/azure-data-fundamentals/",
        "exam": "Microsoft Azure Data Fundamentals",
    },
]

# Chips: a Simple Icons slug renders with its logo, anything else as plain text.
STACK = [
    ("AI & LLM", ["RAG", "Multi-agent systems", "ReACT loops", "Knowledge graphs", "langgraph", "langchain",
                  "OpenAI SDK", "openrouter", "n8n", "pytorch", "tensorflow", "yolo"]),
    ("DATA", ["Microsoft Fabric", "apachekafka", "Redpanda", "postgresql", "SQL Server", "redis", "neo4j", "sqlite",
              "pandas", "apacheavro", "Power BI", "ETL / ELT"]),
    ("CLOUD & OPS", ["AWS S3 · DynamoDB · Kinesis", "Azure", "terraform", "docker", "kubernetes", "k3s", "helm",
                     "githubactions", "gitlab", "prometheus", "grafana"]),
    ("EDGE & EMBEDDED", ["edgeimpulse", "TFLite Micro", "arduino", "espressif", "bluetooth", "wearos", "android",
                         "C++ / NDK / JNI"]),
    ("LANGUAGES", ["python", "typescript", "javascript", "openjdk", "c", "cplusplus", "php", "dart", "C#", "SQL"]),
    ("WEB & QA", ["react", "nextdotjs", "vuedotjs", "nodedotjs", "express", "fastapi", "flask", "laravel", "inertia",
                  "dotnet", "flutter", "pytest", "selenium", "appium"]),
]

# Display names for Simple Icons slugs where the official title reads awkwardly.
LABELS = {
    "openjdk": "Java", "cplusplus": "C++", "nextdotjs": "Next.js", "vuedotjs": "Vue 3", "nodedotjs": "Node.js",
    "dotnet": "ASP.NET Core", "apachekafka": "Kafka", "apacheavro": "Avro", "githubactions": "GitHub Actions",
    "gitlab": "GitLab CI/CD", "openrouter": "OpenRouter", "yolo": "YOLO", "langgraph": "LangGraph",
    "langchain": "LangChain", "k3s": "k3s", "c": "C", "pytest": "pytest", "espressif": "ESP32",
    "bluetooth": "BLE / iBeacon", "wearos": "Wear OS", "edgeimpulse": "Edge Impulse", "laravel": "Laravel 12",
    "inertia": "Inertia", "react": "React", "php": "PHP",
}

FLAGSHIPS = {
    "postmortem": {
        "repo": "Postmortem-Autopilot",
        "tag": "FLAGSHIP  ·  LLM RELIABILITY",
        "title": "Postmortem Autopilot",
        "body": "Rebuilds an incident timeline from logs, alerts, deploys and commits, then writes a postmortem "
                "where **every factual claim is mechanically traceable** to a timestamped source event, "
                "or it doesn't ship. The LLM is fenced between two deterministic planes.",
        "metrics": [("0", "hallucinated", "citations"), ("95%", "minimum claim", "coverage"), ("2", "LLM calls", "per run")],
        "chips": ["python", "langgraph", "neo4j", "docker", "k3s", "helm", "githubactions"],
    },
    "tradepulse": {
        "repo": "tradepulse",
        "tag": "REAL-TIME DATA ENGINEERING",
        "title": "TradePulse",
        "body": "A fully local, production-grade streaming pipeline: synthetic OHLCV ticks flow through "
                "**Redpanda**, get enriched in real time with **VWAP, RSI-14 and anomaly detection**, and land in "
                "S3 Parquet and DynamoDB. Provisioned with **Terraform**, observed with **Prometheus + Grafana**.",
        "metrics": [("4", "CI/CD", "workflows"), ("23+", "unit and", "integration tests"), ("3", "Grafana", "dashboards")],
        "chips": ["python", "apachekafka", "apacheavro", "terraform", "docker", "prometheus", "grafana"],
    },
}

CARDS = {
    "konsol": {
        "repo": "Konsol",
        "tag": "MOBILE  ·  FLUTTER",
        "title": "Konsol",
        "body": "A premium SSH client for mobile: multi-session tabs, keychain-stored Ed25519/RSA keys and "
                "**remote path autocomplete** globbed live over a side SSH channel.",
        "chips": ["flutter", "dart", "SSH", "xterm"],
        "icon": "flutter",
    },
    "football": {
        "repo": "Tunisian_Footbal_DataWarehouse",
        "tag": "DATA WAREHOUSING  ·  OLAP",
        "title": "Tunisian Football DW",
        "body": "Python ETL that collects, cleans and integrates Tunisian league data into a "
                "**constellation schema** for OLAP analytics and Power BI reporting.",
        "chips": ["python", "pandas", "SQL Server", "Power BI"],
        "icon": "pandas",
    },
}

MINI = [
    {"repo": "Champions_League", "title": "Champions League ETL", "icon": "postgresql",
     "body": "2011–2024 UCL data → KPIs → PostgreSQL → Power BI.", "chips": ["python", "postgresql", "Power BI"]},
    {"repo": "RealTime-Fitness-Analyzer", "title": "Fitness Analyzer", "icon": "mediapipe",
     "body": "Real-time rep counting and form feedback from pose landmarks.", "chips": ["mediapipe", "opencv", "python"]},
    {"repo": "Opti-DataCenter-Tunisie", "title": "Data Center MILP", "icon": "python",
     "body": "Energy-cost optimisation under CPU, RAM and storage limits, solved to optimality.",
     "chips": ["PuLP", "LINGO", "python"]},
    {"repo": "swag-labs-mobile-tests", "title": "Mobile Test Suite", "icon": "appium",
     "body": "Appium + pytest suites for login, navigation and app state on Android.", "chips": ["appium", "pytest", "python"]},
    {"repo": "NovaWrite", "title": "Nova Write", "icon": "dotnet",
     "body": "Blog/CMS with role-based access control on ASP.NET Core MVC 8.", "chips": ["dotnet", "EF Core", "SQL Server"]},
    {"repo": "Super_Keyboard", "title": "Super Keyboard", "icon": "cplusplus",
     "body": "A Magic Tiles–style 2D rhythm game written in C++ with SFML.", "chips": ["cplusplus", "SFML"]},
]

HEADINGS = [
    ("experience", "01", "Experience", "2025 — 2026"),
    ("work", "02", "Selected work", "open source"),
    ("certs", "03", "Certifications", "Microsoft · 2026"),
    ("stack", "04", "Stack", "tools in daily use"),
    ("activity", "05", "Activity", "refreshed daily"),
]

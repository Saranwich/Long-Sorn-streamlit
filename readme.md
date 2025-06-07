# 👨🏻‍🏫 Long Sorn (ลองสอน)

> **Super AI Innovation**
>**Team Members:**
- "**Kiadtisak Preechanon** - ??? "         
- "**Kittiphat Noikate**    - ??? "
- "**Suphawadi Poolpuang**  - ??? "
- "**Saranwich Pochai**     - ??? "
- "**Krittikorn Sangthong** - ??? "

---

```
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
📝 Long-Sorn project:
│
├── 📁.github/                          # Houses all GitHub-specific configurations, primarily for CI/CD.
│   └── 📁workflows/                    # Contains CI/CD workflow definition files.
│       ├── frontend_deploy.yml         # CI/CD: Deploys the frontend application to Vercel automatically.
│       ├── backend_ci.yml              # CI: Runs tests for all backend services on every push.
│       └── backend_deploy.yml          # CD: Deploys backend services to the OCI VM.
│
├── 📁backend/                          # Main directory for all server-side Python services.
│   │
│   ├── 📁services/                     # Contains the code for each individual, decoupled microservice.
│   │   │
│   │   ├── 📁api_server/               # 1. Main Backend API Service (FastAPI).
│   │   │   ├── 📁app/                  # Core application source code.
│   │   │   │   ├── 📁routers/          # Holds API endpoint routers (users.py, videos.py).
│   │   │   │   ├── dependencies.py     # Manages dependencies and shared logic for endpoints.
│   │   │   │   └── main.py             # Entry point for the FastAPI application.
│   │   │   ├── 📁tests/                # Unit and integration tests for the API service.
│   │   │   ├── Dockerfile              # Defines the container image for this API service.
│   │   │   └── requirements.txt        # Lists Python dependencies for this service.
│   │   │
│   │   ├── 📁video_worker/             # 2. Background service for video processing.
│   │   │   ├── 📁app/                  # Core application source code for the worker.
│   │   │   │   ├── processor.py        # Contains the main video processing logic using FFmpeg.
│   │   │   │   └── main.py             # Entry point for the worker to pull jobs from the queue.
│   │   │   ├── Dockerfile              # Defines the container image for the video worker.
│   │   │   └── requirements.txt        # Lists Python dependencies for this worker.
│   │   │
│   │   └── 📁ai_orchestrator/          # 3. Service for orchestrating AI/ML tasks.
│   │       ├── 📁app/                  # Core application source code for the AI service.
│   │       │   ├── services/           # Logic for calling external APIs (e.g., Google STT, Gemini).
│   │       │   ├── nlp_custom.py       # Contains the project's custom Natural Language Processing logic.
│   │       │   └── main.py             # Entry point for the AI orchestration service.
│   │       ├── Dockerfile              # Defines the container image for the AI service.
│   │       └── requirements.txt        # Lists Python dependencies for this AI service.
│   │
│   └── 📁shared/                       # Shared Python code used across multiple backend services.
│       ├── 📁db/                       # Manages database connection settings (PostgreSQL).
│       ├── 📁models/                   # Contains shared Pydantic data models.
│       └── 📁core/                     # Core configurations, such as environment variable loading.
│
├── 📁database/                         # Manages database schema and migrations.
│   └── 📁migrations/                   # Stores database schema migration scripts (e.g., for Alembic).
│
├── 📁docs/                             # Contains all project documentation.
│   ├── architecture.png                # The system architecture diagram.
│   ├── setup-guide.md                  # A guide for setting up the development environment.
│   └── api_endpoints.md                # High-level API documentation (supplements Swagger UI).
│
├── 📁frontend/                         # Main directory for the Next.js frontend application.
│   ├── 📁public/                       # Stores static assets like images and fonts.
│   ├── 📁src/                          # Main source code for the frontend application.
│   │   ├── 📁app/                      # App Router directory for pages and layouts.
│   │   ├── 📁components/               # Reusable React components.
│   │   ├── 📁hooks/                    # Custom React hooks.
│   │   └── 📁lib/                      # Library functions, API clients, etc.
│   ├── 📁__tests__/                    # Contains all frontend tests (for Jest).
│   ├── next.config.js                  # Configuration file for Next.js.
│   ├── package.json                    # Defines project metadata and npm dependencies.
│   └── tailwind.config.js              # Configuration file for Tailwind CSS.
│
├── .gitignore                          # Specifies intentionally untracked files to ignore.
├── docker_compose.yml                  # Defines and runs multi-container Docker applications for local development.
└── README.md                           # Main project overview, setup instructions, and general information.
──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
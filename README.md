# ML/MLOps Hands-on Learning Review

> **Scope:** WSL2 → Docker Desktop → Docker fundamentals → Containers → FastAPI ML serving → Dockerfile → Docker Compose → Git/GitHub → GitHub Actions CI → pytest → Docker Build & Push → Docker Hub
>
> **Current status:** CI is complete. Automated deployment (CD) is the next step.

---

## 1. Overall Learning Goal

The goal of this project was to understand the basic MLOps delivery flow by actually building it:

```text
ML Model
   ↓
FastAPI
   ↓
Docker Image
   ↓
Docker Hub
   ↓
GitHub Actions CI
   ↓
Test
   ↓
Docker Build
   ↓
Docker Push
```

The main lesson is not memorizing commands. It is understanding what each component does and how the components connect.

---

## 2. Development Environment

```text
Windows
  │
  ├── VS Code
  │
  └── WSL2
       └── Ubuntu
            │
            ├── Python
            ├── Git
            └── Docker CLI
                    │
                    ▼
              Docker Desktop
                    │
                    ▼
              Docker Engine
```

| Component | Role |
|---|---|
| Windows | Main desktop operating system |
| WSL2 | Linux development environment on Windows |
| Ubuntu | Linux shell and development environment |
| VS Code | Code editor |
| Docker Desktop | Convenient Docker environment on Windows |
| Docker Engine | Core engine that actually runs containers |

### Why WSL2?

MLOps and production server environments are often Linux-based. WSL2 makes it possible to practice Linux-oriented development while keeping Windows as the main desktop OS.

---

## 3. WSL2 and Python

Move to the project directory:

```bash
cd ~/ml-docker
```

Check Python:

```bash
python3 --version
```

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

A virtual environment avoids installing project packages into the system Python environment.

---

## 4. VS Code + WSL

From the WSL terminal:

```bash
cd ~/ml-docker
code .
```

This opens the project in VS Code while keeping the project environment inside WSL.

---

# 5. Core Docker Concepts

## 5.1 The Core Docker Flow

```text
Dockerfile
    ↓ docker build
Image
    ↓ docker run
Container
```

| Term | Meaning |
|---|---|
| Dockerfile | Instructions for building an Image |
| Image | Packaged application and runtime environment |
| Container | Running instance created from an Image |
| Registry | Storage for Docker Images |
| Docker Hub | A widely used Docker Image Registry |
| Compose | Tool for defining and managing Services/Containers with YAML |

### Most important distinction

> **An Image does not run. A Container runs.**

One Image can be used to create multiple Containers.

---

## 6. First Docker Exercise

Create a simple project:

```bash
mkdir docker-test
cd docker-test
echo 'print("Hello from Docker!")' > app.py
```

The `echo` command prints text and `>` redirects the output into a file.

### Dockerfile

```dockerfile
FROM python:3.12
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
```

Build the Image:

```bash
docker build -t my-python-app .
```

Run the Container:

```bash
docker run my-python-app
```

The `.` in `docker build` means the current directory is the build context.

---

# 7. Essential Docker Commands

| Command | Purpose |
|---|---|
| `docker images` | List Images |
| `docker ps` | List running Containers |
| `docker ps -a` | List all Containers |
| `docker stop <container>` | Stop a Container |
| `docker start <container>` | Start an existing Container |
| `docker rm <container>` | Remove a Container |
| `docker rmi <image>` | Remove an Image |
| `docker pull <image>` | Download an Image from a Registry |
| `docker push <image>` | Upload an Image to a Registry |

### `docker run` vs `docker start`

```text
docker run
Image → create a NEW Container → run it

docker start
Existing Container → run it again
```

`docker run` creates a new Container each time. `docker start` reuses an existing stopped Container.

---

# 8. ML Model + FastAPI

Project structure:

```text
ml-docker/
├── .dockerignore
├── .gitignore
├── .venv/
├── Dockerfile
├── app.py
├── model.pkl
├── requirements.txt
├── train.py
├── compose.yml
├── test_app.py
└── .github/
    └── workflows/
        └── ci.yml
```

## 8.1 Training and Serving

```text
train.py
   ↓
model.pkl
   ↓
app.py
   ↓
FastAPI
   ↓
Prediction API
```

`train.py` trains the model and creates `model.pkl`.

`app.py` loads `model.pkl` and exposes a prediction endpoint.

The serving Container does not retrain the model. It uses the already-generated model artifact.

---

# 9. FastAPI

`app.py`:

```python
from fastapi import FastAPI
import pickle

app = FastAPI()

with open("model.pkl", "rb") as f:
    model = pickle.load(f)

@app.get("/")
def home():
    return {"message": "ML model server is running"}

@app.post("/predict")
def predict(data: dict):
    X = [[
        data["area"],
        data["rooms"]
    ]]
    prediction = model.predict(X)[0]
    return {
        "prediction": float(prediction)
    }
```

Run locally:

```bash
uvicorn app:app --reload
```

`app:app` means the `app` object inside `app.py`.

- **FastAPI** defines the API application.
- **Uvicorn** runs that application as an HTTP server.
- `--reload` is mainly for development and restarts the server when source files change.

---

# 10. Swagger

FastAPI automatically provides interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

The `/predict` endpoint was tested with:

```json
{
  "area": 84,
  "rooms": 3
}
```

---

# 11. Dockerfile for the ML API

Final Dockerfile:

```dockerfile
FROM python:3.14.4

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY model.pkl .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Instruction | Meaning |
|---|---|
| `FROM python:3.14.4` | Base Image |
| `WORKDIR /app` | Working directory inside the Container |
| `COPY requirements.txt .` | Copy dependency list |
| `RUN pip install ...` | Install dependencies while building the Image |
| `COPY app.py .` | Copy API source code |
| `COPY model.pkl .` | Copy the trained model |
| `CMD [...]` | Command executed when the Container starts |

Build:

```bash
docker build -t ml-fastapi .
```

---

# 12. Docker Port Mapping

Run:

```bash
docker run -p 8000:8000 ml-fastapi
```

`-p` means:

```text
-p HostPort:ContainerPort
```

Traffic flow:

```text
Browser
   ↓
localhost:8000
   ↓
Host port 8000
   ↓
Container port 8000
   ↓
Uvicorn
```

### What does `0.0.0.0:8000` mean?

When Uvicorn listens on `0.0.0.0:8000`, it listens on port 8000 on all network interfaces inside the Container. It is not the external browser address users should type.

### Running without port mapping

```bash
docker run -d 2fortune/ml-fastapi:1.0
```

The service may run inside the Container, but the host has no published port pointing to Container port 8000.

Use:

```bash
docker run -d -p 8000:8000 2fortune/ml-fastapi:1.0
```

when host access is required.

---

# 13. HTTP Request

Calling `/predict` is an HTTP request, not a local file execution.

Example:

```text
POST http://13.124.XX.XX:8000/predict
Content-Type: application/json

{
    "area": 84,
    "rooms": 3
}
```

Conceptually an HTTP request contains:

```text
Request Line
    ↓
Headers
    ↓
Blank Line
    ↓
Body
```

Python can create such a request with:

```python
requests.post(
    url,
    json={"area": 84, "rooms": 3}
)
```

Swagger's Execute button performs the same basic operation.

---

# 14. Docker Hub

GitHub and Docker Hub have different roles:

| GitHub | Docker Hub |
|---|---|
| Source Code | Docker Image |
| `git push` | `docker push` |
| Git Repository | Image Registry |

Examples:

```bash
docker push 2fortune/ml-fastapi:1.0
docker pull 2fortune/ml-fastapi:1.0
```

Image naming format:

```text
username/repository:tag
```

Example:

```text
2fortune/ml-fastapi:1.0
```

---

# 15. Docker Compose

Example `compose.yml`:

```yaml
services:
  ml-api:
    image: 2fortune/ml-fastapi:1.0
    container_name: ml-api
    ports:
      - "8000:8000"
```

Start:

```bash
docker compose up -d
```

Stop and remove Compose-managed resources:

```bash
docker compose down
```

> **Compose is a tool for defining and managing Services/Containers with YAML.**

## 15.1 `image:` vs `build:`

### `image:`

```yaml
services:
  ml-api:
    image: 2fortune/ml-fastapi:1.0
```

Use an existing Image:

```text
Docker Hub
   ↓ pull
Image
   ↓
Container
```

### `build:`

```yaml
services:
  ml-api:
    build: .
```

Build an Image from the Dockerfile in the current directory:

```text
Dockerfile
   ↓
Image
   ↓
Container
```

### Key rule

```text
build  = how to create an Image
image  = which Image to use
Compose = how to manage Services/Containers
```

---

# 16. Git and GitHub

Basic Git flow:

```text
Working Files
     ↓ git add
Staging Area
     ↓ git commit
Local Repository
     ↓ git push
GitHub
```

Typical commands:

```bash
git init
git add .
git commit -m "message"
git remote add origin <repository>
git push -u origin main
```

After configuring the upstream branch, `git push` is usually enough. `git push origin main` is also valid and explicit.

---

# 17. `.gitignore` vs `.dockerignore`

`.gitignore`:

```text
.venv/
__pycache__/
*.pyc
```

This prevents Git from tracking the listed files.

`.dockerignore`:

```text
.venv
__pycache__
*.pyc
```

This keeps the files out of the Docker build context.

```text
.gitignore
→ Git tracking exclusion

.dockerignore
→ Docker build-context exclusion
```

Neither file deletes the excluded files from the computer.

---

# 18. What Is CI?

CI means **Continuous Integration**.

A basic workflow is:

```text
Developer
    ↓ git push
GitHub
    ↓
GitHub Actions
    ↓
Tests
    ↓
Build
    ↓
Push
```

Important:

> **CI does not inherently block `git push`.**

The code can still reach GitHub. The CI result can instead be used as a gate for later steps such as Image publishing or deployment.

---

# 19. GitHub Actions

GitHub Actions is GitHub's integrated automation platform for CI/CD.

| Tool | Typical characteristic |
|---|---|
| GitHub Actions | Convenient GitHub integration |
| Jenkins | Separate CI/CD server with extensive customization |
| Bamboo | Strong integration with the Atlassian ecosystem |

General structure:

```text
Git Repository
      ↓
CI/CD Tool
      ↓
Build / Test
      ↓
Docker Image
      ↓
Registry
      ↓
Deploy
```

---

# 20. pytest

Test file:

```python
def test_add():
    result = 2 + 3
    assert result == 5
```

Run locally:

```bash
pytest
```

### Deliberate test failure

The test was intentionally changed to:

```python
assert result == 7
```

The CI result became:

```text
Checkout              ✅
Python Setup          ✅
Dependencies          ✅
Run tests              ❌
```

The workflow stopped at the failed test stage.

```text
Test Failure
    ↓
Pipeline Stops
```

---

# 21. GitHub Actions Workflow

File:

```text
.github/workflows/ci.yml
```

Final workflow:

```yaml
name: CI

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Run tests
        run: pytest

      - name: Log in to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: 2fortune/ml-fastapi:latest
```

---

# 22. Understanding `ci.yml`

### `name`

```yaml
name: CI
```

Defines the workflow name.

### `on`

```yaml
on:
  push:
    branches: [main]
```

Runs the workflow when a push occurs on the `main` branch.

### `runs-on`

```yaml
runs-on: ubuntu-latest
```

Runs the job on a GitHub-hosted Ubuntu runner.

### `uses`

```yaml
uses: actions/checkout@v4
```

Uses an existing reusable GitHub Action.

### `run`

```yaml
run: pytest
```

Runs a shell command directly on the runner.

---

# 23. Checkout

```yaml
- name: Checkout code
  uses: actions/checkout@v4
```

Checks out the repository source code onto the temporary GitHub Actions runner.

---

# 24. Python Setup

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.14"
```

Configures Python for the CI job.

---

# 25. Dependency Installation

```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install pytest
```

Installs project dependencies and pytest into the CI environment.

---

# 26. Docker Hub Secrets

Docker Hub credentials should not be hard-coded in the workflow file.

GitHub Repository Secrets:

```text
DOCKERHUB_USERNAME = 2fortune
DOCKERHUB_TOKEN    = Docker Hub Access Token
```

Workflow usage:

```yaml
username: ${{ secrets.DOCKERHUB_USERNAME }}
password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### Security principles

Do not put the Access Token directly into:

- source code
- README files
- public messages
- `ci.yml`

---

# 27. Docker Login

```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

This authenticates the GitHub Actions runner to Docker Hub.

---

# 28. Docker Build + Push

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: 2fortune/ml-fastapi:latest
```

- `context: .` uses the current repository as the Docker build context.
- `push: true` pushes the built Image to the Registry.
- `tags` defines the Image name and tag.

Final Image:

```text
2fortune/ml-fastapi:latest
```

---

# 29. Docker Hub Error Encountered

The first tag used the wrong namespace:

```yaml
tags: 2-fortune/ml-fastapi:latest
```

The actual Docker Hub username is:

```text
2fortune
```

The resulting error was:

```text
denied: requested access to the resource is denied
```

The fix was:

```yaml
tags: 2fortune/ml-fastapi:latest
```

The Image namespace must match the authenticated Docker Hub account.

---

# 30. Final CI Pipeline

```text
                    Developer
                        │
                    git push
                        ▼
                 ┌─────────────┐
                 │   GitHub    │
                 └──────┬──────┘
                        │
                        ▼
              ┌───────────────────┐
              │  GitHub Actions   │
              │                   │
              │  Checkout         │
              │      ↓            │
              │  Python Setup     │
              │      ↓            │
              │  Dependencies     │
              │      ↓            │
              │  pytest           │
              │      ↓            │
              │  Docker Login     │
              │      ↓            │
              │  Docker Build     │
              │      ↓            │
              │  Docker Push      │
              └─────────┬─────────┘
                        │
                        ▼
               ┌─────────────────┐
               │   Docker Hub    │
               │ 2fortune/       │
               │ ml-fastapi      │
               │ :latest         │
               └─────────────────┘
```

---

# 31. CI Success Criteria

All of these stages should pass:

```text
✓ Checkout code
✓ Set up Python
✓ Install dependencies
✓ Run tests
✓ Log in to Docker Hub
✓ Build and push Docker image
```

At this point, the CI hands-on project is complete.

---

# 32. Current Position in the MLOps Lifecycle

A simplified MLOps lifecycle:

```text
Code
  ↓
Test
  ↓
Build
  ↓
Registry
  ↓
Deploy
  ↓
Monitor
```

Current status:

```text
Code
  ↓
Test        ← COMPLETED
  ↓
Build       ← COMPLETED
  ↓
Registry    ← COMPLETED
  ↓
Deploy      ← NEXT
  ↓
Monitor     ← LATER
```

---

# 33. CI vs CD

| Stage | Core Question |
|---|---|
| Git | How do we version the source code? |
| CI | Does the code work, and can we build the Image? |
| Registry | Where do we store the Image? |
| CD | How do we deploy it to the actual environment? |
| Container Runtime | How do we run the Container on the server? |
| Orchestration | How do we manage many Containers? |
| Monitoring | How do we know the service is healthy? |

**Current status: CI completed / CD not yet implemented**

---

# 34. Command Cheat Sheet

## WSL / Python

```bash
cd ~/ml-docker
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Model

```bash
python3 train.py
```

Output:

```text
model.pkl
```

## FastAPI

```bash
uvicorn app:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Docker

```bash
docker build -t ml-fastapi .
docker run -p 8000:8000 ml-fastapi

docker images
docker ps
docker ps -a

docker stop <container>
docker start <container>
docker rm <container>
docker rmi <image>

docker pull 2fortune/ml-fastapi:1.0
docker push 2fortune/ml-fastapi:1.0
```

## Compose

```bash
docker compose up -d
docker compose down
```

## Git

```bash
git status
git add .
git commit -m "message"
git push
```

## CI

```bash
pytest
```

GitHub Actions runs the CI workflow automatically for the configured push event.

---

# 35. Troubleshooting Record

## 35.1 Docker Command Problems

Check:

```text
Is Docker Desktop running?
Is WSL Integration enabled?
Does `docker info` work?
```

## 35.2 Python `pip` Problem

Use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 35.3 scikit-learn Version Warning

If the scikit-learn version used to create `model.pkl` differs from the runtime version, a warning such as `InconsistentVersionWarning` may appear.

Regenerate the model with the current environment:

```bash
python3 train.py
```

Keep the scikit-learn version in `requirements.txt` aligned with the model environment.

## 35.4 Git SSH Authentication

SSH clone/push can fail if an SSH key has not been created or registered with GitHub. HTTPS is another option.

## 35.5 Docker Hub Permission Error

```text
denied: requested access to the resource is denied
```

Check:

1. Docker Hub username
2. Access Token
3. Repository name
4. Image namespace
5. GitHub Secrets
6. Docker login step

For this project:

```text
Docker Hub username = 2fortune
Image = 2fortune/ml-fastapi:latest
```

---

# 36. Core Concepts at a Glance

## Docker

```text
Dockerfile
   ↓ build
Image
   ↓ run
Container
```

## Registry

```text
Local Image
   ↓ docker push
Docker Hub
   ↓ docker pull
Other Server
```

## Compose

```text
compose.yml
   ↓
Service Definition
   ↓
Container Management
```

## Git

```text
Working Tree
   ↓ add
Staging
   ↓ commit
Local Repository
   ↓ push
GitHub
```

## CI

```text
git push
   ↓
GitHub Actions
   ↓
Test
   ↓
Docker Build
   ↓
Docker Push
```

---

# 37. Key Takeaways

1. **Dockerfile → Image → Container**
2. `docker build` = build an Image
3. `docker run` = create and run a new Container
4. `docker start` = start an existing Container
5. `-p Host:Container` = publish/map a port
6. **An Image does not run; a Container runs.**
7. **GitHub = Source Code / Docker Hub = Docker Image**
8. **Compose = Service/Container management**
9. `build` = how to create an Image
10. `image` = which Image to use
11. **CI = automated validation and build after code changes**
12. CI does not inherently block `git push`
13. `uses:` = use an existing GitHub Action
14. `run:` = execute a shell command
15. GitHub Secrets = manage sensitive credentials
16. **pytest succeeds → Docker Build → Docker Push**
17. **CI completion does not mean deployment is complete.**
18. Automated deployment belongs to **CD**

---

# 38. Recommended Next Steps

## Step 1 — CD

Pull the Docker Image from Docker Hub onto a real Linux server:

```text
Docker Hub
    ↓ docker pull
Server
    ↓
docker compose up -d
```

## Step 2 — Image Tagging Strategy

Instead of using only `latest`, use version numbers or Git commit SHA values:

```text
2fortune/ml-fastapi:abc1234
2fortune/ml-fastapi:v1.0.1
```

This makes deployed versions easier to identify.

## Step 3 — Cloud Server

Install Docker on a Linux cloud server and expose the API externally.

## Step 4 — Reverse Proxy / HTTPS

Add Nginx, a domain, and TLS/HTTPS for a more production-oriented architecture.

## Step 5 — Monitoring

Collect metrics such as CPU, memory, API latency, error rate, and logs.

## Step 6 — Kubernetes

When the number of Containers grows, learn Kubernetes concepts such as:

- Deployment
- Scaling
- Self-healing
- Service Discovery
- Rolling Updates

---

# 39. Final Architecture

```text
┌──────────────────────┐
│      Developer       │
│ Python / FastAPI / ML│
└──────────┬───────────┘
           │ git push
           ▼
┌──────────────────────┐
│       GitHub         │
│     Source Code      │
└──────────┬───────────┘
           │ trigger
           ▼
┌───────────────────────────────┐
│       GitHub Actions CI       │
│                               │
│ Checkout                      │
│   ↓                           │
│ Python Setup                  │
│   ↓                           │
│ Dependencies                  │
│   ↓                           │
│ pytest                        │
│   ↓                           │
│ Docker Hub Login              │
│   ↓                           │
│ Docker Build                  │
│   ↓                           │
│ Docker Push                   │
└───────────────┬───────────────┘
                │
                ▼
┌────────────────────────┐
│      Docker Hub        │
│ 2fortune/ml-fastapi    │
│       :latest          │
└────────────┬───────────┘
             │
             │ Next step: CD
             ▼
┌────────────────────────┐
│   Deployment Server    │
│                        │
│ docker pull            │
│ docker compose up -d   │
└────────────────────────┘
```

---

## Conclusion

The most important lesson is the role of each component and the connection between them:

```text
GitHub
  = Source Code

Dockerfile
  = Image build instructions

Docker Image
  = Packaged runtime/application

Container
  = Running Image

Docker Hub
  = Image Registry

Docker Compose
  = Service/Container management

GitHub Actions
  = Automation Pipeline

CI
  = Test + Build + Push

CD
  = Deployment
```

The project now automates:

**code push → automated tests → Docker Image build → Docker Hub push**

The next step is to deploy that Image automatically to a real server and extend the workflow from **CI → CD**.

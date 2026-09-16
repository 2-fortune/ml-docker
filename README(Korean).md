# ML/MLOps 학습 복기 노트

> **범위:** WSL2 → Docker Desktop → Docker 기본 개념 → Container → FastAPI ML Serving → Dockerfile → Docker Compose → Git/GitHub → GitHub Actions CI → pytest → Docker Build & Push → Docker Hub  
> **현재 상태:** CI까지 완료. 실제 서버 자동 배포(CD)는 다음 단계.

---

## 1. 전체 학습 목표

이번 실습의 핵심은 Docker 명령어를 단순 암기하는 것이 아니라,

**ML 모델 → API 서비스 → Docker Image → Registry → 자동 테스트 → 자동 Image Build/Push**

라는 MLOps의 기본 흐름을 직접 만들어 보는 것이었다.

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

---

# 2. 개발 환경

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

| 구성요소 | 역할 |
|---|---|
| Windows | 주 운영체제 |
| WSL2 | Windows에서 Linux 개발 환경 사용 |
| Ubuntu | Linux shell / Python / Git 작업 |
| VS Code | 코드 편집 |
| Docker Desktop | Windows에서 Docker를 편리하게 실행/관리 |
| Docker Engine | 실제 Container를 실행하는 Docker 핵심 엔진 |

### WSL2를 사용하는 이유

MLOps와 서버 환경은 Linux 기반인 경우가 많다.

WSL2를 사용하면 Windows를 유지하면서 Linux 환경에서 Docker, Python, Git 등의 작업을 연습할 수 있다.

---

# 3. WSL2와 Python

## 3.1 프로젝트 이동

```bash
cd ~/ml-docker
```

Python 버전 확인:

```bash
python3 --version
```

Ubuntu에서는 `python` 대신 `python3`가 기본 명령인 경우가 있다.

## 3.2 Python 가상환경

Ubuntu의 externally-managed-environment 정책 때문에 전역 `pip3 install`이 막힐 수 있다.

프로젝트별 가상환경을 사용한다.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

패키지 설치:

```bash
pip install -r requirements.txt
```

---

# 4. VS Code + WSL

WSL 터미널에서:

```bash
cd ~/ml-docker
code .
```

Windows의 VS Code UI를 사용하면서 프로젝트는 WSL Linux 환경에서 작업할 수 있다.

---

# 5. Docker 핵심 개념

## 5.1 Docker의 핵심 흐름

```text
Dockerfile
    ↓ docker build
Image
    ↓ docker run
Container
```

### 핵심 정의

| 용어 | 의미 | 기억법 |
|---|---|---|
| Dockerfile | Image를 만드는 방법을 정의한 파일 | Image 제작 설명서 |
| Image | 실행에 필요한 환경과 애플리케이션을 묶은 패키지 | 실행 준비 패키지 |
| Container | Image를 실제 실행한 인스턴스 | 실행 중인 인스턴스 |
| Registry | Docker Image 저장소 | Image 저장소 |
| Docker Hub | 대표적인 Docker Image Registry | Image 공유 저장소 |
| Compose | 여러 Service/Container를 YAML로 관리하는 도구 | Container 관리 도구 |

### 가장 중요한 구분

> **Image는 실행되지 않는다. Container가 실행된다.**

하나의 Image로 여러 Container를 만들 수 있다.

---

# 6. 첫 Docker 실습

프로젝트 생성:

```bash
mkdir docker-test
cd docker-test
```

파일 생성:

```bash
echo 'print("Hello from Docker!")' > app.py
```

`echo`는 문자열을 출력하고 `>`는 출력을 파일로 저장한다.

즉 위 명령은 `app.py`를 만들고 내용을 기록한다.

---

## 6.1 첫 Dockerfile

```dockerfile
FROM python:3.12
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
```

### 의미

- `FROM`: 기반 Image
- `WORKDIR`: Container 내부 작업 디렉터리
- `COPY`: 파일 복사
- `CMD`: Container 실행 시 기본 명령

---

## 6.2 Image Build

```bash
docker build -t my-python-app .
```

여기서 `.`은 현재 디렉터리를 Docker build context로 사용한다.

---

## 6.3 Container 실행

```bash
docker run my-python-app
```

---

# 7. Docker 명령어

| 명령어 | 역할 |
|---|---|
| `docker images` | Image 목록 |
| `docker ps` | 실행 중 Container |
| `docker ps -a` | 모든 Container |
| `docker stop <container>` | Container 중지 |
| `docker start <container>` | 기존 Container 다시 시작 |
| `docker rm <container>` | Container 삭제 |
| `docker rmi <image>` | Image 삭제 |
| `docker pull <image>` | Registry에서 Image 다운로드 |
| `docker push <image>` | Registry로 Image 업로드 |

## `docker run`과 `docker start` 차이

```text
docker run
Image → 새 Container 생성 → 실행

docker start
기존 Container → 다시 실행
```

따라서 `docker run`은 매번 새로운 Container를 생성한다.

---

# 8. ML 모델 + FastAPI

프로젝트 구조:

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

---

## 8.1 Training과 Serving

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

`train.py`는 모델을 학습하고 `model.pkl`을 생성한다.

`app.py`는 `model.pkl`을 읽어 API로 예측 서비스를 제공한다.

이번 실습에서는 Serving Container에서 다시 학습하지 않고, 이미 생성된 `model.pkl`을 Image에 포함했다.

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

---

## 9.1 FastAPI와 Uvicorn

```text
FastAPI
  ↓
API 애플리케이션 작성

Uvicorn
  ↓
FastAPI 애플리케이션을 HTTP 서버로 실행
```

실행:

```bash
uvicorn app:app --reload
```

`app:app`은:

```text
app.py
  ↓
app 객체
```

를 의미한다.

`--reload`는 개발 중 코드 변경 시 서버를 자동 재시작한다.

---

# 10. Swagger

FastAPI는 API 문서를 자동 생성한다.

```text
http://127.0.0.1:8000/docs
```

`/predict`에서 다음 JSON으로 테스트했다.

```json
{
  "area": 84,
  "rooms": 3
}
```

---

# 11. Dockerfile로 ML API 만들기

최종 Dockerfile:

```dockerfile
FROM python:3.14.4

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY model.pkl .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 각 명령

| 명령 | 의미 |
|---|---|
| `FROM python:3.14.4` | Python 3.14.4 기반 Image |
| `WORKDIR /app` | Container 내부 작업 위치 |
| `COPY requirements.txt .` | 의존성 목록 복사 |
| `RUN pip install ...` | Image 생성 과정에서 패키지 설치 |
| `COPY app.py .` | API 코드 복사 |
| `COPY model.pkl .` | 학습된 모델 복사 |
| `CMD [...]` | Container 시작 시 실행 |

Build:

```bash
docker build -t ml-fastapi .
```

---

# 12. Docker Port

실행:

```bash
docker run -p 8000:8000 ml-fastapi
```

`-p`는:

```text
-p HostPort:ContainerPort
```

이다.

```text
Browser
   ↓
localhost:8000
   ↓
Host 8000
   ↓
Container 8000
   ↓
Uvicorn
```

---

## 12.1 `0.0.0.0:8000`

Uvicorn 로그의:

```text
http://0.0.0.0:8000
```

은 Container 내부에서 모든 네트워크 인터페이스에 대해 8000 포트를 listen한다는 의미다.

외부 사용자가 접속할 목적지 주소를 의미하는 것은 아니다.

---

## 12.2 Port 매핑 없이 실행

```bash
docker run -d 2fortune/ml-fastapi:1.0
```

Container 내부에서 서버가 실행되더라도 Host의 8000과 연결되지 않는다.

따라서 일반적으로:

```text
localhost:8000
```

으로 접근할 수 없다.

외부 접근이 필요하면:

```bash
docker run -d -p 8000:8000 2fortune/ml-fastapi:1.0
```

---

# 13. HTTP Request

`/predict`는 파일을 실행하는 것이 아니라 HTTP Request를 보내는 것이다.

```text
POST http://13.124.XX.XX:8000/predict
Content-Type: application/json

{
    "area": 84,
    "rooms": 3
}
```

개념적으로:

```text
Request Line
    ↓
Headers
    ↓
Blank Line
    ↓
Body
```

Python:

```python
requests.post(
    url,
    json={"area": 84, "rooms": 3}
)
```

이나 Swagger의 Execute가 이러한 HTTP Request를 만들어 서버로 보낸다고 이해하면 된다.

---

# 14. Docker Hub

GitHub와 Docker Hub의 역할을 구분한다.

| GitHub | Docker Hub |
|---|---|
| Source Code 저장 | Docker Image 저장 |
| `git push` | `docker push` |
| Git Repository | Image Registry |

예:

```bash
docker push 2fortune/ml-fastapi:1.0
docker pull 2fortune/ml-fastapi:1.0
```

Image 이름:

```text
사용자명/Repository:Tag
```

예:

```text
2fortune/ml-fastapi:1.0
```

---

# 15. Docker Compose

`compose.yml`:

```yaml
services:
  ml-api:
    image: 2fortune/ml-fastapi:1.0
    container_name: ml-api
    ports:
      - "8000:8000"
```

실행:

```bash
docker compose up -d
```

종료:

```bash
docker compose down
```

Compose는 Image나 Container 자체가 아니다.

> **Compose = 여러 Service/Container를 YAML로 정의하고 관리하는 도구**

---

## 15.1 `image:` vs `build:`

### `image:`

```yaml
services:
  ml-api:
    image: 2fortune/ml-fastapi:1.0
```

이미 존재하는 Image를 사용한다.

예:

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

현재 디렉터리의 Dockerfile을 이용해 Image를 만든다.

```text
Dockerfile
   ↓
Image
   ↓
Container
```

### 핵심

```text
build = Image를 만드는 방법

image = 사용할 Image

Compose = Container/Service를 관리하는 방법
```

---

# 16. Git과 GitHub

Git의 기본 흐름:

```text
Working Files
     ↓ git add
Staging Area
     ↓ git commit
Local Repository
     ↓ git push
GitHub
```

기본 명령:

```bash
git init
git add .
git commit -m "message"
git remote add origin <repository>
git push -u origin main
```

첫 Push에서 `-u`로 upstream을 설정하면 이후에는:

```bash
git push
```

만 사용해도 된다.

명시적으로:

```bash
git push origin main
```

을 사용해도 된다.

---

# 17. `.gitignore`와 `.dockerignore`

`.gitignore`:

```text
.venv/
__pycache__/
*.pyc
```

Git에 추적하지 않을 파일을 지정한다.

`.dockerignore`:

```text
.venv
__pycache__
*.pyc
```

Docker build context에서 제외한다.

### 차이

```text
.gitignore
→ Git 관리 대상에서 제외

.dockerignore
→ Docker Build Context에서 제외
```

둘 다 실제 파일을 삭제하는 것은 아니다.

---

# 18. CI란?

CI = Continuous Integration

코드가 변경될 때마다 자동으로 테스트와 검증을 수행하는 방식이다.

```text
Developer
    ↓ git push
GitHub
    ↓
GitHub Actions
    ↓
Test
    ↓
Build
    ↓
Push
```

중요한 점:

> **CI는 git push 자체를 막는 장치가 아니다.**

코드는 GitHub에 올라갈 수 있다.

대신 CI 실패 시 이후 단계가 실행되지 않도록 Workflow를 구성할 수 있다.

---

# 19. GitHub Actions

GitHub Actions는 GitHub에 통합된 CI/CD 자동화 플랫폼이다.

비교:

| 도구 | 특징 |
|---|---|
| GitHub Actions | GitHub와 통합되어 편리 |
| Jenkins | 독립적인 CI/CD 서버, 높은 Customization |
| Bamboo | Atlassian 생태계와 연계 |

일반적인 구조:

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

테스트 파일:

```python
def test_add():
    result = 2 + 3
    assert result == 5
```

로컬에서:

```bash
pytest
```

실행한다.

---

## 20.1 CI 테스트 실패 실습

일부러:

```python
assert result == 7
```

로 변경했다.

결과:

```text
Checkout              ✅
Python Setup          ✅
Dependencies          ✅
Run tests              ❌
```

테스트가 실패하면서 이후 단계로 진행하지 않았다.

이 실습을 통해:

```text
테스트 실패
    ↓
Pipeline 중단
```

을 직접 확인했다.

---

# 21. CI Workflow

파일:

```text
.github/workflows/ci.yml
```

최종 구성:

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

# 22. `ci.yml` 상세 해석

## `name`

```yaml
name: CI
```

Workflow 이름이다.

## `on`

```yaml
on:
  push:
    branches: [main]
```

`main` branch에 Push가 발생하면 Workflow를 실행한다.

## `runs-on`

```yaml
runs-on: ubuntu-latest
```

GitHub가 제공하는 Ubuntu Runner에서 실행한다.

## `uses`

```yaml
uses: actions/checkout@v4
```

이미 만들어진 GitHub Action을 사용한다.

## `run`

```yaml
run: pytest
```

Runner에서 shell 명령을 직접 실행한다.

---

# 23. Checkout

```yaml
- name: Checkout code
  uses: actions/checkout@v4
```

GitHub Repository의 소스 코드를 GitHub Actions Runner로 가져온다.

---

# 24. Python 설정

```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: "3.14"
```

CI Runner에 Python 환경을 설정한다.

---

# 25. Dependency 설치

```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt
    pip install pytest
```

CI 환경에 프로젝트 실행에 필요한 Python 패키지와 pytest를 설치한다.

---

# 26. Docker Hub Secret

Docker Hub 인증정보를 Workflow 파일에 직접 쓰지 않는다.

GitHub Repository Secrets:

```text
DOCKERHUB_USERNAME = 2fortune
DOCKERHUB_TOKEN    = Docker Hub Access Token
```

Workflow:

```yaml
username: ${{ secrets.DOCKERHUB_USERNAME }}
password: ${{ secrets.DOCKERHUB_TOKEN }}
```

### 보안 원칙

Access Token의 실제 값은:

- 코드에 작성하지 않는다.
- README에 작성하지 않는다.
- 채팅에 공개하지 않는다.
- Workflow에 평문으로 작성하지 않는다.

---

# 27. Docker Login

```yaml
- name: Log in to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}
```

GitHub Actions Runner가 Docker Hub에 인증하도록 한다.

---

# 28. Docker Build + Push

최종:

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: 2fortune/ml-fastapi:latest
```

### `context: .`

현재 GitHub Repository를 Docker Build Context로 사용한다.

따라서 Dockerfile이 필요한 파일을 가져올 수 있다.

### `push: true`

Image Build 후 Docker Registry로 Push한다.

### `tags`

```yaml
tags: 2fortune/ml-fastapi:latest
```

생성할 Image의 이름과 Tag를 지정한다.

---

# 29. 실제 경험한 Docker Hub 오류

처음에는:

```yaml
tags: 2-fortune/ml-fastapi:latest
```

처럼 작성했다.

하지만 실제 Docker Hub 계정명은:

```text
2fortune
```

이다.

따라서:

```text
2-fortune/ml-fastapi
```

가 아니라:

```text
2fortune/ml-fastapi
```

이어야 한다.

오류:

```text
denied: requested access to the resource is denied
```

### 해결

```yaml
tags: 2fortune/ml-fastapi:latest
```

Docker Hub username과 Image namespace가 일치해야 한다.

---

# 30. 최종 CI Pipeline

현재 완성된 구조:

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

# 31. CI 성공 조건

GitHub Actions에서 다음 단계가 모두 성공하면 현재 CI는 정상이다.

```text
✓ Checkout code
✓ Set up Python
✓ Install dependencies
✓ Run tests
✓ Log in to Docker Hub
✓ Build and push Docker image
```

그리고 Docker Hub에서:

```text
2fortune/ml-fastapi:latest
```

Image가 확인되면 최종 CI 실습이 완료된 것이다.

---

# 32. MLOps 관점에서 현재 위치

전체 MLOps를 단순화하면:

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

이번 실습은 여기까지 완료했다.

```text
Code
  ↓
Test        ← 완료
  ↓
Build       ← 완료
  ↓
Registry    ← 완료
  ↓
Deploy      ← 다음 단계
  ↓
Monitor     ← 이후 단계
```

---

# 33. CI와 CD 구분

| 단계 | 핵심 질문 |
|---|---|
| Git | 코드를 어떻게 버전 관리하는가? |
| CI | 코드가 정상인가? Image를 만들 수 있는가? |
| Registry | Image를 어디에 저장하는가? |
| CD | 실제 서버에 어떻게 배포하는가? |
| Container Runtime | 서버에서 Container를 어떻게 실행하는가? |
| Orchestration | Container가 많아지면 어떻게 관리하는가? |
| Monitoring | 서비스가 정상인지 어떻게 감시하는가? |

현재는 **CI 완료 / CD 미완료** 상태다.

---

# 34. 전체 명령어 복기

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

결과:

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

CI에서는 GitHub Actions가 자동 실행한다.

---

# 35. 문제 해결 기록

## 35.1 Docker 명령 문제

확인할 것:

```text
Docker Desktop 실행 여부
WSL Integration 설정
docker info
```

## 35.2 Python `pip` 문제

전역 설치 대신:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 35.3 scikit-learn 버전 경고

`model.pkl` 생성 환경과 실행 환경의 scikit-learn 버전이 다르면:

```text
InconsistentVersionWarning
```

이 발생할 수 있다.

현재 환경에 맞춰 모델을 다시 생성하고:

```bash
python3 train.py
```

`requirements.txt` 버전도 일치시키는 것이 좋다.

## 35.4 Git SSH 인증

SSH Key가 준비되지 않았으면 GitHub SSH clone/push가 실패할 수 있다.

HTTPS를 사용하거나 SSH Key를 생성해 GitHub에 등록한다.

## 35.5 Docker Hub 권한 오류

```text
denied: requested access to the resource is denied
```

확인 항목:

1. Docker Hub username
2. Access Token
3. Repository 이름
4. Image namespace
5. GitHub Secret
6. Docker Login 성공 여부

이번 실습에서는:

```text
Docker Hub username = 2fortune
Image = 2fortune/ml-fastapi:latest
```

로 맞춰 해결했다.

---

# 36. 한눈에 보는 핵심 개념

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
Service 정의
   ↓
Container 관리
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

# 37. 가장 중요한 암기 문장

1. **Dockerfile → Image → Container**
2. `docker build` = Image 생성
3. `docker run` = 새 Container 생성 + 실행
4. `docker start` = 기존 Container 다시 실행
5. `-p Host:Container` = 포트 연결
6. **Image는 실행되지 않고 Container가 실행된다.**
7. **GitHub = Source Code / Docker Hub = Docker Image**
8. **Compose = Container/Service 관리**
9. `build` = Image를 만드는 방법
10. `image` = 사용할 Image
11. **CI = 코드 변경 후 자동 검증/Build**
12. CI는 `git push` 자체를 막는 것이 아니다.
13. `uses:` = 기존 GitHub Action 사용
14. `run:` = shell 명령 실행
15. GitHub Secrets = 인증정보 등 민감정보 관리
16. **pytest 성공 → Docker Build → Docker Push**
17. **CI가 끝났다고 배포가 끝난 것은 아니다.**
18. 실제 서버 자동 배포는 **CD**의 영역이다.

---

# 38. 다음 학습 순서

## STEP 1 — CD

Docker Hub의 Image를 실제 Linux 서버에서 가져온다.

```text
Docker Hub
    ↓ docker pull
Server
    ↓
docker compose up -d
```

## STEP 2 — Image Tag 전략

현재:

```text
latest
```

이외에 Git Commit SHA나 버전 번호를 사용해 어떤 코드가 배포되었는지 추적한다.

예:

```text
2fortune/ml-fastapi:abc1234
2fortune/ml-fastapi:v1.0.1
```

## STEP 3 — Cloud Server

EC2 같은 Linux 서버에 Docker를 설치하고 외부에서 API를 호출한다.

## STEP 4 — Reverse Proxy / HTTPS

Nginx, Domain, TLS 등을 연결해 Production API 구조로 확장한다.

## STEP 5 — Monitoring

CPU, Memory, API latency, error rate, logs 등을 수집한다.

## STEP 6 — Kubernetes

Container가 많아졌을 때:

- 배포
- Scaling
- Self-healing
- Service Discovery
- Rolling Update

등을 관리한다.

---

# 39. 최종 전체 그림

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
             │ 다음 단계: CD
             ▼
┌────────────────────────┐
│   Deployment Server    │
│                        │
│ docker pull            │
│ docker compose up -d   │
└────────────────────────┘
```

---

## 결론

이번 실습에서 가장 중요한 것은 개별 명령어보다 **각 구성요소의 역할과 연결 관계**다.

```text
GitHub
  = Source Code

Dockerfile
  = Image 제작 방법

Docker Image
  = 실행 패키지

Container
  = 실행 중인 Image

Docker Hub
  = Image Registry

Docker Compose
  = Container/Service 관리

GitHub Actions
  = 자동화 Pipeline

CI
  = Test + Build + Push

CD
  = 실제 환경 Deploy
```

현재까지의 실습은 **"코드를 Push하면 자동으로 테스트하고, 성공하면 Docker Image를 만들어 Docker Hub에 올리는 과정"**까지 완성한 것이다.

다음 단계에서 이 Image를 실제 서버에 자동으로 배포하면 **CI → CD** 전체 흐름으로 확장된다.

# AI Resume Screening System - UML Diagrams

## 1. Class Diagram

```mermaid
classDiagram
    %% Core Services
    class EmbeddingService {
        -SentenceTransformer model
        +__init__(model_name: str)
        +encode(texts: list~str~) np.ndarray
        +encode_query(query: str) np.ndarray
    }

    class ResumeParser {
        <<static>>
        +extract_text_from_pdf(file_path: str) str
        +extract_text_from_docx(file_path: str) str
        +extract_text_from_txt(file_path: str) str
        +parse_resume(file_path: str) Optional~str~
    }

    class JinaRerankerService {
        -str api_key
        -str base_url
        +__init__(api_key: str)
        +rerank(query: str, documents: list~str~, top_n: int) list~dict~
    }

    class GeminiService {
        -genai.Client client
        -str model_id
        +__init__(api_key: str)
        +generate_jina_reasoning(resume_text: str, job_description: str, jina_score: float) str
        +analyze_candidate(resume_text: str, job_description: str) dict
        +compare_candidates(candidate1_name: str, candidate1_resume: str, candidate1_jina_score: float, candidate2_name: str, candidate2_resume: str, candidate2_jina_score: float, job_description: str) dict
        +extract_score(analysis_text: str)$ int
    }

    class ChromaDBClient {
        -chromadb.PersistentClient client
        -chromadb.Collection collection
        +__init__(db_path: str)
        +add_resumes(ids: list~str~, embeddings: list~list~float~~, documents: list~str~, metadatas: list~dict~)
        +query(query_embedding: list~float~, n_results: int) QueryResult
        +clear()
    }

    %% Configuration
    class Settings {
        +str gemini_api_key
        +str jina_api_key
        +str embedding_model
        +str chroma_db_path
        +str upload_dir
        +str job_description_dir
        +str screening_results_dir
    }

    %% Pydantic Models - Requests
    class ScreeningRequest {
        +str job_description
        +int top_n
    }

    class ComparisonRequest {
        +str candidate1_name
        +str candidate2_name
    }

    %% Pydantic Models - Responses
    class CandidateScore {
        +str name
        +Optional~str~ email
        +float score
        +float jina_score
        +Optional~str~ jina_reasoning
        +int gemini_score
        +str gemini_analysis
        +Optional~str~ thinking_process
        +Optional~str~ resume_text
    }

    class ScreeningResponse {
        +list~CandidateScore~ top_candidates
        +int total_processed
        +float processing_time
        +str job_description
    }

    class ComparisonResponse {
        +str candidate1_name
        +str candidate2_name
        +float candidate1_jina_score
        +float candidate2_jina_score
        +int candidate1_gemini_score
        +int candidate2_gemini_score
        +str comparison
    }

    %% FastAPI Router
    class APIRouter {
        +screen_resumes(job_description: str, job_description_file: File, top_n: int, resumes: list~File~) ScreeningResponse
        +compare_candidates(request: ComparisonRequest) ComparisonResponse
        +get_state() dict
        +health_check() dict
        +get_db_status() dict
        +clear_database() dict
        +root() dict
    }

    %% FastAPI Application
    class FastAPIApp {
        +str title
        +str version
        +include_router(router: APIRouter, prefix: str, tags: list~str~)
    }

    %% Streamlit Application
    class StreamlitApp {
        +render_screening_tab()
        +render_comparison_tab()
        +render_database_tab()
        +upload_files()
        +call_screening_api()
        +display_results()
    }

    %% Relationships
    FastAPIApp --> APIRouter: includes
    APIRouter --> Settings: uses
    APIRouter --> EmbeddingService: depends on
    APIRouter --> ResumeParser: depends on
    APIRouter --> JinaRerankerService: depends on
    APIRouter --> GeminiService: depends on
    APIRouter --> ChromaDBClient: depends on
    APIRouter ..> ScreeningRequest: accepts
    APIRouter ..> ComparisonRequest: accepts
    APIRouter ..> ScreeningResponse: returns
    APIRouter ..> ComparisonResponse: returns
    ScreeningResponse *-- CandidateScore: contains
    StreamlitApp --> APIRouter: HTTP requests
```

---

## 2. Sequence Diagram - Resume Screening Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant API as FastAPI Router
    participant Parser as ResumeParser
    participant Embed as EmbeddingService
    participant DB as ChromaDBClient
    participant Jina as JinaRerankerService
    participant Gemini as GeminiService
    participant FS as File System

    User->>UI: Upload JD + Resumes
    UI->>API: POST /api/v1/screen

    Note over API: Stage 0: Parse Job Description
    API->>Parser: parse_resume(jd_file)
    Parser-->>API: job_description_text
    API->>FS: Save JD to ./data/jd/latest_jd.txt

    Note over API: Stage 1: Parse & Embed Resumes
    loop For each resume file
        API->>FS: Save to ./data/resumes/{filename}
        API->>Parser: parse_resume(resume_file)
        Parser->>Parser: Detect file type (PDF/DOCX/TXT)
        alt PDF
            Parser->>Parser: extract_text_from_pdf()
        else DOCX
            Parser->>Parser: extract_text_from_docx()
        else TXT
            Parser->>Parser: extract_text_from_txt()
        end
        Parser-->>API: resume_text
    end

    API->>Embed: encode(resume_texts)
    Embed->>Embed: BGE-M3 encoding
    Embed-->>API: resume_embeddings (1024-dim)

    API->>DB: add_resumes(ids, embeddings, texts, metadatas)
    DB->>DB: Store in ChromaDB

    API->>Embed: encode_query(job_description)
    Embed-->>API: jd_embedding

    Note over API: Stage 2: Vector Search + Reranking
    API->>DB: query(jd_embedding, n_results=50)
    DB->>DB: Cosine similarity search
    DB-->>API: top_50_candidates

    API->>Jina: rerank(jd, top_50_texts, top_n=10)
    Jina->>Jina: Call Jina API
    Jina-->>API: reranked_top_10 (with scores)

    Note over API: Stage 3: AI Analysis (Parallel)
    par For each top candidate
        API->>Gemini: generate_jina_reasoning(resume, jd, jina_score)
        Gemini-->>API: jina_reasoning

        API->>Gemini: analyze_candidate(resume, jd)
        Gemini->>Gemini: Gemini 2.5 Pro analysis
        Gemini-->>API: {gemini_score, analysis}
    end

    Note over API: Save Results
    API->>API: Build ScreeningResponse
    API->>FS: Save to ./data/screening_results/latest_screening.json
    API-->>UI: ScreeningResponse (top_candidates, total_processed, processing_time)

    UI->>UI: Display results in table
    UI-->>User: Show top candidates with scores
```

---

## 3. Sequence Diagram - Candidate Comparison Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit UI
    participant API as FastAPI Router
    participant State as Server State
    participant Gemini as GeminiService

    User->>UI: Select 2 candidates
    User->>UI: Click "Compare"
    UI->>API: POST /api/v1/compare
    Note over UI,API: ComparisonRequest(candidate1_name, candidate2_name)

    API->>State: Load last_screening_result
    State-->>API: List of CandidateScore objects

    API->>API: Find candidate1 by name
    API->>API: Find candidate2 by name

    alt Candidate not found
        API-->>UI: 404 Not Found
        UI-->>User: Error: Candidate not found
    end

    API->>Gemini: compare_candidates(c1_name, c1_resume, c1_jina_score, c2_name, c2_resume, c2_jina_score, jd)
    Gemini->>Gemini: Gemini 2.5 Pro comparison
    Gemini-->>API: {comparison_text}

    API->>API: Build ComparisonResponse
    API-->>UI: ComparisonResponse

    UI->>UI: Display side-by-side comparison
    UI-->>User: Show scores and AI comparison
```

---

## 4. Activity Diagram - Resume Screening Process

```mermaid
flowchart TD
    Start([User Uploads JD + Resumes]) --> ParseJD{Job Description<br/>Provided?}

    ParseJD -->|File| ExtractJD[Extract Text from JD File]
    ParseJD -->|Text| UseJDText[Use JD Text Directly]
    ParseJD -->|None| LoadJD[Load from ./data/jd/latest_jd.txt]

    ExtractJD --> SaveJD[Save JD to File System]
    UseJDText --> SaveJD
    LoadJD --> SaveJD

    SaveJD --> CheckResumes{New Resumes<br/>Uploaded?}

    CheckResumes -->|Yes| ParseResumes[Parse Resume Files<br/>PDF/DOCX/TXT]
    CheckResumes -->|No| LoadFromDB[Load Existing Resumes<br/>from ChromaDB]

    ParseResumes --> SaveResumes[Save to ./data/resumes/]
    SaveResumes --> CheckDuplicates{Already in<br/>ChromaDB?}

    CheckDuplicates -->|New| GenerateEmbeddings[Generate BGE-M3 Embeddings<br/>1024-dim vectors]
    CheckDuplicates -->|Duplicate| SkipEmbedding[Skip Embedding]

    GenerateEmbeddings --> StoreDB[(Store in ChromaDB<br/>with metadata)]
    SkipEmbedding --> LoadFromDB
    LoadFromDB --> StoreDB

    StoreDB --> EmbedJD[Generate JD Embedding]

    EmbedJD --> VectorSearch[ChromaDB Vector Search<br/>Cosine Similarity<br/>Top 50]

    VectorSearch --> JinaRerank[Jina Reranker API<br/>Rerank Top 50<br/>Return Top N]

    JinaRerank --> ParallelAnalysis{For Each Top<br/>Candidate}

    ParallelAnalysis --> GenerateReasoning[Gemini: Generate<br/>Jina Reasoning]
    ParallelAnalysis --> AnalyzeCandidate[Gemini: Analyze Candidate<br/>Score 0-100]

    GenerateReasoning --> CollectResults[Collect All<br/>CandidateScore Objects]
    AnalyzeCandidate --> CollectResults

    CollectResults --> SortResults[Sort by Jina Score]

    SortResults --> SaveResults[Save to JSON<br/>./data/screening_results/]

    SaveResults --> ReturnResponse[Return ScreeningResponse]

    ReturnResponse --> DisplayUI[Display in Streamlit UI]

    DisplayUI --> End([End])

    style Start fill:#90EE90
    style End fill:#FFB6C1
    style VectorSearch fill:#87CEEB
    style JinaRerank fill:#DDA0DD
    style GenerateReasoning fill:#F0E68C
    style AnalyzeCandidate fill:#F0E68C
    style StoreDB fill:#FFD700
```

---

## 5. Use Case Diagram

```mermaid
flowchart TB
    subgraph System["AI Resume Screening System"]
        UC1[Upload Job Description]
        UC2[Upload Resumes]
        UC3[Screen Resumes]
        UC4[View Screening Results]
        UC5[Compare Two Candidates]
        UC6[View Database Status]
        UC7[Clear Database]
        UC8[Download Results as JSON]
        UC9[View Candidate Details]
        UC10[Restore Previous Results]
    end

    subgraph External["External APIs"]
        Jina[Jina Reranker API]
        Gemini[Google Gemini API]
    end

    subgraph Storage["Data Storage"]
        ChromaDB[(ChromaDB<br/>Vector Database)]
        FileSystem[(File System)]
    end

    User((HR Manager/<br/>Recruiter))
    Admin((System Admin))

    User --> UC1
    User --> UC2
    User --> UC3
    User --> UC4
    User --> UC5
    User --> UC9
    User --> UC10
    User --> UC8

    Admin --> UC6
    Admin --> UC7

    UC3 -.includes.-> UC1
    UC3 -.includes.-> UC2
    UC5 -.requires.-> UC3
    UC9 -.extends.-> UC4

    UC3 --> Jina
    UC3 --> Gemini
    UC5 --> Gemini

    UC3 --> ChromaDB
    UC3 --> FileSystem
    UC6 --> ChromaDB
    UC7 --> ChromaDB
    UC7 --> FileSystem
    UC10 --> FileSystem
```

---

## 6. Component Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend Layer"]
        Streamlit[Streamlit Web UI<br/>app.py]
    end

    subgraph API["API Layer"]
        FastAPI[FastAPI Application<br/>main.py]
        Router[API Router<br/>routes.py]
        Config[Configuration<br/>config.py]
    end

    subgraph Services["Business Logic Layer"]
        Embedding[Embedding Service<br/>BGE-M3]
        Parser[Resume Parser<br/>PDF/DOCX/TXT]
        Reranker[Jina Reranker Service]
        LLM[Gemini LLM Service]
    end

    subgraph Data["Data Layer"]
        ChromaDB[(ChromaDB Client<br/>Vector Database)]
        FileSystem[(File System<br/>./data/)]
    end

    subgraph External["External Services"]
        JinaAPI[Jina Reranker API]
        GeminiAPI[Google Gemini API]
    end

    Streamlit -->|HTTP REST| FastAPI
    FastAPI --> Router
    Router --> Config

    Router --> Embedding
    Router --> Parser
    Router --> Reranker
    Router --> LLM

    Embedding --> ChromaDB
    Parser --> FileSystem
    ChromaDB --> FileSystem

    Reranker -->|HTTPS| JinaAPI
    LLM -->|HTTPS| GeminiAPI

    style Streamlit fill:#90EE90
    style FastAPI fill:#87CEEB
    style ChromaDB fill:#FFD700
    style JinaAPI fill:#DDA0DD
    style GeminiAPI fill:#F0E68C
```

---

## 7. State Diagram - Server State Management

```mermaid
stateDiagram-v2
    [*] --> Uninitialized: Server Start

    Uninitialized --> Restoring: First API Call

    Restoring --> LoadingJD: Check ./data/jd/
    LoadingJD --> LoadingResumes: JD Loaded
    LoadingJD --> LoadingResumes: JD Not Found (empty state)

    LoadingResumes --> LoadingResults: Query ChromaDB
    LoadingResults --> Initialized: Load latest_screening.json
    LoadingResults --> Initialized: No Previous Results

    Initialized --> Processing: Screening Request
    Processing --> Embedding: Parse Files
    Embedding --> VectorSearch: Generate Embeddings
    VectorSearch --> Reranking: Query ChromaDB
    Reranking --> AIAnalysis: Jina Rerank
    AIAnalysis --> Saving: Gemini Analysis
    Saving --> Initialized: Save Results

    Initialized --> Comparing: Comparison Request
    Comparing --> Initialized: Return Comparison

    Initialized --> Clearing: Clear Database Request
    Clearing --> Uninitialized: Delete All Data

    Initialized --> [*]: Server Shutdown
```

---

## Diagram Descriptions

### 1. Class Diagram
Shows all main classes in the system including:
- Service classes (EmbeddingService, ResumeParser, JinaRerankerService, GeminiService, ChromaDBClient)
- Configuration (Settings)
- Request/Response models (Pydantic schemas)
- FastAPI application structure
- Streamlit UI component

### 2. Sequence Diagrams
- **Resume Screening Flow**: End-to-end process from file upload to AI analysis
- **Candidate Comparison Flow**: Process for comparing two selected candidates

### 3. Activity Diagram
Detailed workflow of the resume screening process including:
- Job description handling
- Resume parsing and embedding
- Vector search with ChromaDB
- Jina reranking
- Parallel Gemini AI analysis
- Result storage

### 4. Use Case Diagram
User interactions with the system:
- Primary actors: HR Manager/Recruiter and System Admin
- External systems: Jina API, Gemini API
- Data storage: ChromaDB and File System

### 5. Component Diagram
System architecture showing:
- Frontend (Streamlit)
- API Layer (FastAPI)
- Business Logic (Services)
- Data Layer (ChromaDB + File System)
- External APIs

### 6. State Diagram
Server state lifecycle:
- Initialization and restoration
- Processing states
- Data persistence

---

## How to View These Diagrams

### Option 1: GitHub/GitLab
Upload this file to GitHub/GitLab - they render Mermaid diagrams automatically.

### Option 2: VS Code
Install the "Markdown Preview Mermaid Support" extension.

### Option 3: Online Viewer
Copy and paste the Mermaid code to: https://mermaid.live/

### Option 4: Export as Images
Use Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i diagrams.md -o diagrams.pdf
```

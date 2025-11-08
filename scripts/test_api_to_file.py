import httpx
import os
import time
import json

# 채용 공고 읽기
with open("data/jd/job_description.txt", "r", encoding="utf-8") as f:
    job_description = f.read()

# 이력서 파일 수집
resume_files = []
resume_dir = "data/resumes"
for filename in os.listdir(resume_dir):
    if filename.endswith(".docx"):
        filepath = os.path.join(resume_dir, filename)
        resume_files.append(filepath)

# API 호출
files = []
for resume_path in resume_files:
    with open(resume_path, "rb") as f:
        files.append(
            (
                "resumes",
                (
                    os.path.basename(resume_path),
                    f.read(),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ),
            )
        )

data = {"job_description": job_description, "top_n": 5}

start_time = time.time()

response = httpx.post(
    "http://localhost:8000/api/v1/screen", files=files, data=data, timeout=300.0
)

end_time = time.time()

# 결과를 파일로 저장
with open("test_result.json", "w", encoding="utf-8") as f:
    if response.status_code == 200:
        result = response.json()
        json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Success! Status: {response.status_code}")
        print(f"Processing time: {result['processing_time']:.2f}s")
        print(f"Total processed: {result['total_processed']}")
        print("\nResult saved to: test_result.json")
        print("\nTop candidates:")
        for i, c in enumerate(result["top_candidates"], 1):
            print(f"{i}. {c['name']} - Score: {c['score']:.4f}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

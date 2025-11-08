import httpx
import os
import time

# 채용 공고 읽기
with open("data/jd/job_description.txt", "r", encoding="utf-8") as f:
    job_description = f.read()

print("=== AI Resume Screening 테스트 ===\n")
print("채용 공고:")
print(job_description)
print("\n" + "=" * 50 + "\n")

# 이력서 파일 수집
resume_files = []
resume_dir = "data/resumes"
for filename in os.listdir(resume_dir):
    if filename.endswith(".docx"):
        filepath = os.path.join(resume_dir, filename)
        resume_files.append(filepath)

print(f"업로드할 이력서: {len(resume_files)}개")
for resume in resume_files:
    print(f"  - {os.path.basename(resume)}")

print("\n분석 시작...\n")

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

if response.status_code == 200:
    result = response.json()

    print("✅ 분석 완료!")
    print(f"처리 시간: {result['processing_time']:.2f}초")
    print(f"총 처리: {result['total_processed']}명\n")

    print("=" * 50)
    print("상위 5명 결과")
    print("=" * 50 + "\n")

    for i, candidate in enumerate(result["top_candidates"], 1):
        print(f"\n{'='*50}")
        print(f"🏆 {i}순위: {candidate['name']}")
        print(f"{'='*50}")
        print(f"점수: {candidate['score']:.4f}")
        print(f"\n{candidate['gemini_analysis']}")
        print()

else:
    print(f"❌ API 오류: {response.status_code}")
    print(response.text)

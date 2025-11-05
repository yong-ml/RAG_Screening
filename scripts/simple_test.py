import httpx
import os
import json

# 채용공고 파일 업로드 테스트
jd_file_path = "data/jd/job_description.txt"
resume_dir = "data/resumes"

resume_files = []
for filename in os.listdir(resume_dir):
    if filename.endswith('.docx'):
        filepath = os.path.join(resume_dir, filename)
        resume_files.append(filepath)

files = []

# 채용공고 파일
with open(jd_file_path, 'rb') as f:
    files.append(('job_description_file', (os.path.basename(jd_file_path), f.read(), 'text/plain')))

# 이력서 파일들
for resume_path in resume_files:
    with open(resume_path, 'rb') as f:
        files.append(('resumes', (os.path.basename(resume_path), f.read(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')))

data = {"top_n": 5}

response = httpx.post(
    "http://localhost:8000/api/v1/screen",
    files=files,
    data=data,
    timeout=300.0
)

if response.status_code == 200:
    result = response.json()

    # 결과 저장
    with open("test_result_improved.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Success! Status: {response.status_code}")
    print(f"Processing time: {result['processing_time']:.2f}s")
    print(f"Total processed: {result['total_processed']}")
    print(f"\nTop candidates (by Jina):")

    for i, c in enumerate(result['top_candidates'], 1):
        print(f"{i}. {c['name']}")
        print(f"   Jina Score: {c['jina_score']:.4f}")
        print(f"   Gemini Score: {c['gemini_score']}/100")

    # Gemini 점수로 정렬
    sorted_by_gemini = sorted(result['top_candidates'], key=lambda x: x.get('gemini_score', 0), reverse=True)

    print(f"\nTop candidates (by Gemini):")
    for i, c in enumerate(sorted_by_gemini, 1):
        print(f"{i}. {c['name']}")
        print(f"   Gemini Score: {c['gemini_score']}/100")
        print(f"   Jina Score: {c['jina_score']:.4f}")

    # 두 지원자 비교
    print(f"\nComparing top 2 candidates...")
    compare_response = httpx.post(
        "http://localhost:8000/api/v1/compare",
        json={"candidate1_index": 0, "candidate2_index": 1},
        timeout=120.0
    )

    if compare_response.status_code == 200:
        comparison = compare_response.json()
        print(f"Comparison: {comparison['candidate1_name']} vs {comparison['candidate2_name']}")

        # 비교 결과 저장
        with open("comparison_result.json", "w", encoding="utf-8") as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)

        print("\nResults saved:")
        print("  - test_result_improved.json")
        print("  - comparison_result.json")
    else:
        print(f"Comparison failed: {compare_response.status_code}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)

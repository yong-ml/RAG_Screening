import httpx
import os
import time
import json

print("=== Improved Features Test ===\n")

# 1. 채용공고 파일 업로드 테스트
print("1. Testing Job Description File Upload...")

jd_file_path = "data/jd/job_description.txt"
resume_dir = "data/resumes"

# 이력서 파일 수집
resume_files = []
for filename in os.listdir(resume_dir):
    if filename.endswith('.docx'):
        filepath = os.path.join(resume_dir, filename)
        resume_files.append(filepath)

print(f"   - Job description file: {jd_file_path}")
print(f"   - Resume files: {len(resume_files)}")

# API 호출 준비
files = []

# 채용공고 파일 추가
with open(jd_file_path, 'rb') as f:
    files.append(('job_description_file', (os.path.basename(jd_file_path), f.read(), 'text/plain')))

# 이력서 파일 추가
for resume_path in resume_files:
    with open(resume_path, 'rb') as f:
        files.append(('resumes', (os.path.basename(resume_path), f.read(), 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')))

data = {
    "top_n": 5
}

print("\n2. Analyzing resumes...")
start_time = time.time()

response = httpx.post(
    "http://localhost:8000/api/v1/screen",
    files=files,
    data=data,
    timeout=300.0
)

if response.status_code == 200:
    result = response.json()

    print(f"\n✓ Analysis complete!")
    print(f"   Processing time: {result['processing_time']:.2f}s")
    print(f"   Total processed: {result['total_processed']}")

    # 점수 비교 테스트
    print("\n3. Score Comparison:")
    print("   " + "="*80)
    print(f"   {'Rank':<6} {'Name':<20} {'Jina Score':<15} {'Gemini Score':<15}")
    print("   " + "="*80)

    for i, c in enumerate(result['top_candidates'], 1):
        jina = c.get('jina_score', 0)
        gemini = c.get('gemini_score', 0)
        print(f"   {i:<6} {c['name']:<20} {jina:.4f}{'':<10} {gemini}/100")

    # Gemini 점수로 재정렬
    sorted_by_gemini = sorted(result['top_candidates'], key=lambda x: x.get('gemini_score', 0), reverse=True)

    print("\n4. Sorted by Gemini Score:")
    print("   " + "="*80)
    print(f"   {'Rank':<6} {'Name':<20} {'Gemini Score':<15} {'Jina Score':<15}")
    print("   " + "="*80)

    for i, c in enumerate(sorted_by_gemini, 1):
        gemini = c.get('gemini_score', 0)
        jina = c.get('jina_score', 0)
        print(f"   {i:<6} {c['name']:<20} {gemini}/100{'':<10} {jina:.4f}")

    # 두 지원자 비교 테스트
    print("\n5. Testing Candidate Comparison...")
    print(f"   Comparing: {result['top_candidates'][0]['name']} vs {result['top_candidates'][1]['name']}")

    compare_response = httpx.post(
        "http://localhost:8000/api/v1/compare",
        json={
            "candidate1_index": 0,
            "candidate2_index": 1
        },
        timeout=120.0
    )

    if compare_response.status_code == 200:
        comparison = compare_response.json()
        print(f"\n✓ Comparison complete!")
        print(f"   Candidate 1: {comparison['candidate1_name']}")
        print(f"   Candidate 2: {comparison['candidate2_name']}")
        print("\n   Comparison Analysis:")
        print("   " + "="*80)
        # 첫 500자만 출력
        comp_text = comparison['comparison'][:500]
        for line in comp_text.split('\n'):
            print(f"   {line}")
        print("   ...")
        print("   (Full comparison saved to comparison_result.json)")

        # 비교 결과 저장
        with open("comparison_result.json", "w", encoding="utf-8") as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)
    else:
        print(f"   ✗ Comparison failed: {compare_response.status_code}")
        print(f"   {compare_response.text}")

    # 전체 결과 저장
    with open("improved_test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "="*80)
    print("All tests completed successfully!")
    print("Results saved to:")
    print("  - improved_test_result.json")
    print("  - comparison_result.json")
    print("="*80)

else:
    print(f"Error: {response.status_code}")
    print(response.text)

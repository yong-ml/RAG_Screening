from google import genai
import re


class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-pro"

    def generate_jina_reasoning(
        self, resume_text: str, job_description: str, jina_score: float
    ) -> str:
        """Jina 점수 기반 간단한 매칭 요약 생성"""

        prompt = f"""
당신은 HR 컨설턴트입니다. 절대 과장되게 표현하지 말고 객관적인 태도로 대답하세요. 이력서와 채용공고의 Jina 매칭 점수가 {jina_score:.3f}점입니다.

## 채용공고:
{job_description}

## 이력서:
{resume_text}

위 점수를 기반으로 **2-3문장**으로 간단히 설명하세요:
- 왜 이 점수를 받았는지
- 어떤 부분이 매칭되는지/되지 않는지

형식: 간단명료한 2-3문장 (불릿 포인트 없이)
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id, contents=prompt
            )
            return response.text.strip()
        except Exception:
            return f"매칭 점수: {jina_score:.3f} (의미론적 유사도 기반)"

    def analyze_candidate(
        self, resume_text: str, job_description: str
    ) -> dict[str, str]:
        """Gemini로 후보자 분석"""

        prompt = f"""
당신은 전문 HR 컨설턴트입니다. 절대 과장되게 표현하지 말고 객관적인 태도로 아래 이력서와 채용공고를 분석하여 상세한 평가를 제공하세요.

## 채용공고:
{job_description}

## 이력서:
{resume_text}

다음 형식으로 분석하세요:

### 1. 필수 요구사항 매칭 (5점 만점)
- 각 필수 요구사항별 평가

### 2. 우대사항 매칭
- 우대사항별 충족 여부

### 3. 강점
- 3가지 핵심 강점

### 4. 약점
- 보완이 필요한 부분

### 5. 종합 평가 (100점 만점)
- 최종 점수와 근거
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id, contents=prompt
            )
            analysis_text = response.text

            # 점수 추출
            score = self.extract_score(analysis_text)

            return {
                "analysis": analysis_text,
                "thinking_process": None,
                "gemini_score": score,
            }
        except Exception as e:
            return {
                "analysis": f"분석 중 오류 발생: {str(e)}",
                "thinking_process": None,
                "gemini_score": 0,
            }

    @staticmethod
    def extract_score(analysis_text: str) -> int:
        """분석 텍스트에서 점수 추출 (100점 만점)"""
        # 패턴들: "점수: 92/100", "92/100", "점수: 92", "92점" 등
        # 마크다운 bold 마커(**) 고려
        patterns = [
            r"점수[:\s*]*(\d+)\s*/\s*100",  # "점수:** 92/100" 형식
            r"(\d+)\s*/\s*100",
            r"점수[:\s*]*(\d+)점",  # "점수:** 92점" 형식 (bold 마커 포함)
            r"총점[:\s*]*(\d+)\s*/\s*100",
            r"총점[:\s*]*(\d+)점",  # "총점:** 55점" 형식
        ]

        for pattern in patterns:
            match = re.search(pattern, analysis_text)
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    return score

        # 점수를 찾지 못한 경우 기본값
        return 0

    def compare_candidates(
        self,
        candidate1_name: str,
        candidate1_resume: str,
        candidate1_jina_score: float,
        candidate2_name: str,
        candidate2_resume: str,
        candidate2_jina_score: float,
        job_description: str,
    ) -> dict[str, str]:
        """두 지원자 비교 분석"""

        prompt = f"""
당신은 전문 HR 컨설턴트입니다. 절대 과장되게 표현하지 말고 객관적인 태도로 아래 두 지원자를 채용공고에 맞춰 비교 분석하세요.

## 채용공고:
{job_description}

## 지원자 1: {candidate1_name}
- **Jina 매칭 점수**: {candidate1_jina_score:.3f} (의미론적 유사도)

{candidate1_resume}

## 지원자 2: {candidate2_name}
- **Jina 매칭 점수**: {candidate2_jina_score:.3f} (의미론적 유사도)

{candidate2_resume}

**참고**: Jina 매칭 점수는 채용공고와 이력서 간의 의미론적 유사도를 나타냅니다.
높은 점수는 키워드와 문맥이 잘 매칭됨을 의미합니다.

다음 형식으로 비교 분석하세요:

### 1. Jina 매칭 점수 분석
- 점수 차이가 의미하는 것
- 각 지원자의 키워드/문맥 매칭도

### 2. {candidate1_name}의 주요 강점
- 3가지 핵심 강점

### 3. {candidate2_name}의 주요 강점
- 3가지 핵심 강점

### 4. {candidate1_name}의 주요 약점
- 보완이 필요한 부분

### 5. {candidate2_name}의 주요 약점
- 보완이 필요한 부분

### 6. 기술 스택 비교
- 필수 요구사항 충족도
- 우대사항 충족도
- 기술적 차별점

### 7. 종합 비교 및 추천
- 어떤 지원자가 더 적합한지
- 그 이유 (Jina 매칭도와 실질적 역량을 모두 고려)
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id, contents=prompt
            )
            return {"comparison": response.text}
        except Exception as e:
            return {"comparison": f"비교 분석 중 오류 발생: {str(e)}"}

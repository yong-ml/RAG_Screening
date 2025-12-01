from google import genai
import re


class GeminiService:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-pro"

    def generate_candidate_summary(
        self, resume_text: str, job_description: str
    ) -> str:
        """이력서 기반 간단한 요약 생성"""

        prompt = f"""
당신은 HR 컨설턴트입니다. 이력서와 채용공고를 비교하여 지원자의 적합성을 평가하세요.

## 채용공고:
{job_description}

## 이력서:
{resume_text}

**2-3문장**으로 지원자의 핵심 역량과 직무 적합성을 간단히 요약하세요.
- **점수를 직접 언급하지 마세요.** (예: "0.731점은..." 등 점수 설명 금지)
- 지원자가 가진 핵심 기술과 경험, 그리고 JD와의 매칭 포인트 위주로 작성하세요.
- "지원자는..." 또는 "이 지원자는..." 으로 시작하는 자연스러운 문장으로 작성하세요.

형식: 간단명료한 2-3문장 (불릿 포인트 없이 줄글로 작성)
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id, 
                contents=prompt,
                config={"temperature": 0.0}
            )
            return response.text.strip()
        except Exception:
            return "요약 생성 실패"

    def extract_criteria(self, job_description: str) -> list[str]:
        """JobAnalysisAgent: JD에서 핵심 평가 기준 추출"""
        prompt = f"""
당신은 채용 직무 분석 전문가(Job Analysis Agent)입니다.
아래 채용공고(JD)를 분석하여 지원자를 평가할 **핵심 기준(Criteria) 5~7가지**를 추출하세요.

## 채용공고:
{job_description}

## 지침:
1. **필수 기술(Hard Skills)**과 **핵심 역량(Soft Skills/Culture)**을 모두 포함하세요.
2. 각 기준은 명확하고 구체적이어야 합니다. (예: "Python 숙련도" 대신 "Python 기반 백엔드 개발 경험 (3년 이상)")
3. 중요도 순으로 나열하세요.

## 출력 형식:
- 각 기준을 한 줄에 하나씩 작성하세요.
- 번호나 불릿 포인트 없이 텍스트만 작성하세요.
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_id, 
                contents=prompt,
                config={"temperature": 0.0}
            )
            criteria = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            return criteria
        except Exception as e:
            print(f"Criteria Extraction Error: {e}")
            return ["직무 적합성", "기술 스택 일치도", "관련 프로젝트 경험"]

    def evaluate_candidate_criteria(self, resume_text: str, criterion: str) -> dict:
        """ScreeningAgent: 특정 기준에 대해 후보자 평가 (Deep Reasoning & Flexible Skill)"""
        prompt = f"""
당신은 냉철한 채용 평가자(Screening Agent)입니다.
지원자의 이력서가 아래 **평가 기준**을 충족하는지 **증거 기반(Evidence-based)**으로 검증하세요.

## 평가 기준:
{criterion}

## 이력서:
{resume_text}

## 평가 지침:
1. **심층 추론(Deep Reasoning)**: 단순히 키워드가 있는지가 아니라, **프로젝트 경험이나 경력 기술서의 문맥(Context)**에서 해당 역량이 발휘되었는지 확인하세요.
2. **유연한 기술 평가(Flexible Skill)**: JD에 명시된 기술이 없더라도, **동등한 수준의 대체 기술(Equivalent Tech)**(예: TensorFlow <-> PyTorch, AWS <-> Azure)이 있다면 인정하고 점수를 부여하세요. 단, 차이점은 언급하세요.
3. **증거 제시**: 점수의 근거가 되는 이력서 내의 구체적인 문장이나 프로젝트명을 인용하세요.

## 출력 형식 (JSON):
{{
    "score": 0~10 사이의 정수 (0: 없음, 5: 보통, 10: 탁월),
    "reasoning": "평가 근거 (한글 1-2문장)",
    "evidence": "이력서 내 발견된 증거 (없으면 '없음')"
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.0
                }
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            return {"score": 0, "reasoning": f"평가 중 오류: {str(e)}", "evidence": "N/A"}

    def detect_over_optimization(self, resume_text: str, job_description: str) -> dict:
        """AuditAgent: 과적합/어뷰징 감지"""
        prompt = f"""
당신은 채용 부정행위 감사관(Audit Agent)입니다.
이 지원자가 채용 시스템을 속이기 위해 **이력서를 과도하게 최적화(Over-optimization)**했는지 검사하세요.

## 채용공고:
{job_description}

## 이력서:
{resume_text}

## 감지 항목:
1. **키워드 스터핑**: 문맥 없이 키워드만 나열하거나, 흰색 글씨로 숨기는 행위(텍스트 추출 시 보임).
2. **JD 복사**: 채용공고의 문장을 그대로 복사해서 자소서에 넣은 경우.
3. **부자연스러운 반복**: 특정 기술 용어가 비정상적으로 많이 반복되는 경우.

## 출력 형식 (JSON):
{{
    "suspicion_score": 0~100 사이 정수 (0: 정상, 100: 매우 의심됨),
    "flagged_issues": ["감지된 문제 1", "감지된 문제 2"],
    "analysis": "종합 의견 (한글)"
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0.0
                }
            )
            import json
            return json.loads(response.text)
        except Exception as e:
            return {"suspicion_score": 0, "flagged_issues": [], "analysis": "감지 실패"}

    def analyze_candidate(
        self, resume_text: str, job_description: str, criteria: list[str] = None
    ) -> dict[str, str]:
        """Coordinator: 멀티 에이전트 조율 및 최종 리포트 생성"""
        
        # 1. 기준이 없으면 추출 (보통 tasks.py에서 넘겨줌)
        if not criteria:
            criteria = self.extract_criteria(job_description)

        # 2. 각 기준별 평가 (ScreeningAgent)
        evaluations = []
        total_score = 0
        for criterion in criteria:
            result = self.evaluate_candidate_criteria(resume_text, criterion)
            evaluations.append({
                "criterion": criterion,
                "score": result.get("score", 0),
                "reasoning": result.get("reasoning", ""),
                "evidence": result.get("evidence", "")
            })
            total_score += result.get("score", 0)

        # 3. 과적합 감지 (AuditAgent)
        audit_result = self.detect_over_optimization(resume_text, job_description)
        suspicion_score = audit_result.get("suspicion_score", 0)

        # 4. 최종 점수 계산 (100점 만점 환산)
        # 기준 개수에 따라 정규화. 감점 요인(의심 점수) 반영 가능.
        avg_score = (total_score / len(criteria)) * 10 if criteria else 0
        final_score = max(0, min(100, avg_score - (suspicion_score * 0.2))) # 의심 점수의 20%만큼 감점

        # 5. 분석 리포트 생성 (Markdown)
        analysis_md = "## 📋 상세 평가 리포트\n\n"
        
        if suspicion_score >= 30:
            analysis_md += f"> [!WARNING]\n> **⚠️ 과적합 의심 (점수: {suspicion_score})**\n> {audit_result.get('analysis', '')}\n\n"

        analysis_md += "### 🎯 기준별 평가\n"
        for eval_item in evaluations:
            score_icon = "🟢" if eval_item['score'] >= 8 else "🟡" if eval_item['score'] >= 5 else "🔴"
            analysis_md += f"- **{score_icon} {eval_item['criterion']}** ({eval_item['score']}/10)\n"
            analysis_md += f"  - *근거*: {eval_item['reasoning']}\n"
            if eval_item['evidence'] != '없음':
                analysis_md += f"  - *증거*: `{eval_item['evidence']}`\n"
            analysis_md += "\n"

        return {
            "analysis": analysis_md,
            "thinking_process": (
                f"1. 기준 분석: {len(criteria)}개 핵심 역량 도출 완료\n"
                f"2. 정밀 평가: 각 기준별 증거 기반 검증 수행\n"
                f"3. 신뢰도 검증: 과적합/어뷰징 탐지 (의심 점수: {suspicion_score}점)\n"
                f"4. 최종 점수: {int(final_score)}점 (의심 점수 반영 후)"
            ),
            "gemini_score": int(final_score),
            "criteria_breakdown": evaluations, # DB 스키마가 지원한다면 저장, 아니면 무시됨
            "audit_result": audit_result
        }

    # extract_score 메서드는 더 이상 필요하지 않음

    def compare_candidates(
        self,
        candidate1_name: str,
        candidate1_resume: str,
        candidate1_gemini_score: int,
        candidate1_analysis: str,
        candidate2_name: str,
        candidate2_resume: str,
        candidate2_gemini_score: int,
        candidate2_analysis: str,
        job_description: str,
    ) -> dict[str, str]:
        """두 지원자 비교 분석 (Gemini 점수 및 분석 반영)"""

        prompt = f"""
당신은 공정한 채용 위원회 의장(Hiring Committee Chair)입니다.
이미 개별 스크리닝을 통해 두 지원자에 대한 평가가 완료되었습니다.
이제 채용공고(JD)와 **이전 스크리닝 결과**를 바탕으로 두 지원자를 **1:1 정밀 비교**하여 최종 결론을 내려야 합니다.

## 채용공고:
{job_description}

## 지원자 1: {candidate1_name}
- **기존 점수**: {candidate1_gemini_score}/100
- **기존 분석 요약**:
{candidate1_analysis}

## 지원자 2: {candidate2_name}
- **기존 점수**: {candidate2_gemini_score}/100
- **기존 분석 요약**:
{candidate2_analysis}

## 비교 지침:
1. **일관성 유지**: 기존 스크리닝 점수와 분석 내용을 존중하세요. 점수가 더 높은 지원자가 비교에서도 우위를 점해야 하는 것이 원칙입니다. 단, 직접 비교를 통해 점수만으로는 보이지 않던 결정적인 차이가 발견된다면 이를 명시하고 순위를 뒤집을 수 있습니다.
2. **증거 기반 비교**: 단순히 "누가 좋다"가 아니라, 이력서 내의 **구체적인 증거(프로젝트, 성과, 기술 스택)**를 들어 설명하세요.
3. **서론 생략**: "공정한 채용 위원회 의장으로서..." 와 같은 인사말이나 자기소개를 **절대 포함하지 마세요**. 바로 분석 내용으로 시작하세요.

## 출력 형식 (Markdown):

### 1. 핵심 비교 요약
(두 지원자의 핵심적인 차이점을 3-4문장으로 요약)

### 2. 상세 1:1 비교
#### [기준 1: 기술 역량 및 경험]
- **우위**: {candidate1_name} / {candidate2_name} / 대등
- **분석**: (상세 비교 내용)

#### [기준 2: 직무 적합성 및 잠재력]
- **우위**: {candidate1_name} / {candidate2_name} / 대등
- **분석**: (상세 비교 내용)

### 3. 강점 및 약점 분석
#### 👤 {candidate1_name}
- **강점**:
  - (강점 1)
  - (강점 2)
- **약점**:
  - (약점 1)

#### 👤 {candidate2_name}
- **강점**:
  - (강점 1)
  - (강점 2)
- **약점**:
  - (약점 1)

### 4. 최종 결론
- **최종 추천**: {candidate1_name} / {candidate2_name}
- **결정적 이유**: (지원자의 실질적 역량과 잠재력을 종합한 결론)
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_id, 
                contents=prompt,
                config={"temperature": 0.0}
            )
            return {"comparison": response.text}
        except Exception as e:
            return {"comparison": f"비교 분석 중 오류 발생: {str(e)}"}

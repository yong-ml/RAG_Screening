import streamlit as st
import httpx
import pandas as pd
from typing import List

st.set_page_config(
    page_title="AI Resume Screening",
    page_icon="📄",
    layout="wide"
)

# 환경 설정
API_URL = "http://localhost:8000/api/v1"

st.title("🚀 AI Resume Screening System")
st.markdown("HR 담당자를 위한 지능형 이력서 스크리닝 시스템")

# 서버 상태 로드 (앱 시작 시 1회)
if 'server_state_loaded' not in st.session_state:
    try:
        response = httpx.get(f"{API_URL}/state", timeout=10.0)
        if response.status_code == 200:
            server_state = response.json()
            st.session_state['server_state'] = server_state

            # 기존 스크리닝 결과가 있으면 세션에 저장
            if server_state['has_screening_result'] and server_state['screening_result']:
                result = server_state['screening_result']
                st.session_state['results'] = {
                    'top_candidates': result['candidates'],
                    'total_processed': result['total_processed'],
                    'processing_time': result['processing_time'],
                    'job_description': result['job_description']
                }
                st.session_state['candidates'] = result['candidates']
                st.session_state['sort_method'] = "Jina Reranker 점수 (코사인 유사도)"
        else:
            st.session_state['server_state'] = {
                'has_job_description': False,
                'resume_count': 0,
                'resume_filenames': [],
                'has_screening_result': False
            }
    except:
        st.session_state['server_state'] = {
            'has_job_description': False,
            'resume_count': 0,
            'resume_filenames': [],
            'has_screening_result': False
        }

    st.session_state['server_state_loaded'] = True

server_state = st.session_state.get('server_state', {})

# 사이드바: 입력
with st.sidebar:
    st.header("📋 입력")

    # 기존 데이터 표시
    if server_state.get('has_job_description'):
        st.success(f"✅ 채용공고 저장됨")
        st.caption(f"미리보기: {server_state.get('job_description_preview', '')}...")

    if server_state.get('resume_count', 0) > 0:
        st.success(f"✅ 저장된 이력서: {server_state['resume_count']}개")
        with st.expander("파일 목록 보기"):
            for filename in server_state.get('resume_filenames', []):
                st.text(f"• {filename}")

    st.markdown("---")

    # 채용 공고 입력 방식 선택
    if server_state.get('has_job_description'):
        jd_help_text = "이미 저장된 채용공고가 있습니다. 새로 입력하면 교체됩니다."
    else:
        jd_help_text = "채용공고를 입력해주세요."

    st.caption(jd_help_text)

    jd_input_method = st.radio(
        "채용 공고 입력 방식",
        ["입력 안 함 (기존 사용)", "텍스트 직접 입력", "파일 업로드 (TXT/PDF/DOCX)"]
    )

    if jd_input_method == "텍스트 직접 입력":
        job_description = st.text_area(
            "채용 공고",
            height=200,
            placeholder="채용 공고 전체 내용을 입력하세요..."
        )
        jd_file = None
    elif jd_input_method == "파일 업로드 (TXT/PDF/DOCX)":
        jd_file = st.file_uploader(
            "채용 공고 파일",
            type=['txt', 'pdf', 'docx']
        )
        job_description = None
    else:
        job_description = None
        jd_file = None

    top_n = st.slider(
        "상위 몇 명?",
        min_value=5,
        max_value=50,
        value=10
    )

    # 정렬 방식 선택
    sort_method = st.radio(
        "정렬 기준",
        ["Jina Reranker 점수 (코사인 유사도)", "Gemini AI 평가 점수 (100점)"]
    )

    # 이력서 업로드
    if server_state.get('resume_count', 0) > 0:
        st.caption("새로운 이력서를 추가하면 기존 이력서와 함께 스크리닝됩니다.")

    uploaded_files = st.file_uploader(
        "이력서 업로드 (PDF/DOCX)",
        type=['pdf', 'docx'],
        accept_multiple_files=True,
        help="새 이력서를 추가하거나, 처음 업로드하세요."
    )

    analyze_button = st.button(
        "🔍 분석 시작",
        type="primary",
        use_container_width=True
    )


def show_results(results, candidates, sort_method):
    """결과 화면을 표시하는 함수"""
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(
        ["📊 상위 N명", "🔍 비교", "💡 추천 근거"]
    )

    # Tab 1: 상위 N명 리스트
    with tab1:
        st.subheader(f"상위 {len(candidates)}명")

        df_data = []
        for i, c in enumerate(candidates):
            if sort_method == "Gemini AI 평가 점수 (100점)":
                df_data.append({
                    "순위": i + 1,
                    "이름": c['name'],
                    "Gemini 점수": f"{c['gemini_score']}/100",
                    "Jina 점수": f"{c['jina_score']:.3f}",
                })
            else:
                df_data.append({
                    "순위": i + 1,
                    "이름": c['name'],
                    "Jina 점수": f"{c['jina_score']:.3f}",
                    "Gemini 점수": f"{c['gemini_score']}/100",
                })

        df = pd.DataFrame(df_data)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    # Tab 2: 비교 화면
    with tab2:
        st.subheader("후보자 비교")

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            candidate1_idx = st.selectbox(
                "지원자 1",
                range(len(candidates)),
                format_func=lambda i: f"{candidates[i]['name']} (Gemini: {candidates[i]['gemini_score']}점)"
            )

        with col2:
            candidate2_idx = st.selectbox(
                "지원자 2",
                range(len(candidates)),
                format_func=lambda i: f"{candidates[i]['name']} (Gemini: {candidates[i]['gemini_score']}점)",
                index=1 if len(candidates) > 1 else 0
            )

        with col3:
            compare_button = st.button("🔍 비교하기", type="primary")

        if compare_button:
            if candidate1_idx == candidate2_idx:
                st.warning("다른 지원자를 선택하세요!")
            else:
                with st.spinner("AI가 두 지원자를 비교 분석 중입니다..."):
                    compare_response = httpx.post(
                        f"{API_URL}/compare",
                        json={
                            "candidate1_index": candidate1_idx,
                            "candidate2_index": candidate2_idx
                        },
                        timeout=120.0
                    )

                    if compare_response.status_code == 200:
                        comparison = compare_response.json()
                        st.markdown("---")
                        st.markdown(f"## 🆚 {comparison['candidate1_name']} vs {comparison['candidate2_name']}")
                        st.markdown(comparison['comparison'])
                    else:
                        st.error(f"비교 분석 실패: {compare_response.text}")

        # 개별 지원자 상세 정보
        st.markdown("---")
        st.subheader("개별 지원자 상세 분석")
        for i, candidate in enumerate(candidates[:5]):
            with st.expander(f"🏆 {i+1}순위: {candidate['name']} (Jina: {candidate['jina_score']:.3f}, Gemini: {candidate['gemini_score']}점)"):
                st.markdown(candidate['gemini_analysis'])

    # Tab 3: 추천 근거
    with tab3:
        st.subheader("AI 추천 근거")

        for i, candidate in enumerate(candidates[:3]):
            st.markdown(f"### 🏆 {i+1}순위: {candidate['name']}")
            st.markdown(f"**Jina Reranker 점수**: {candidate['jina_score']:.4f}")
            st.markdown(f"**Gemini 평가 점수**: {candidate['gemini_score']}/100")
            st.markdown(candidate['gemini_analysis'])

            if candidate.get('thinking_process'):
                with st.expander("🧠 AI 사고 과정 보기 (Thinking Mode)"):
                    st.text(candidate['thinking_process'])

            st.divider()


# 메인 로직
if analyze_button:
    # 입력 검증
    if jd_input_method == "텍스트 직접 입력" and not job_description:
        st.error("채용 공고를 입력하세요!")
    elif jd_input_method == "파일 업로드 (TXT/PDF/DOCX)" and not jd_file:
        st.error("채용 공고 파일을 업로드하세요!")
    elif jd_input_method == "입력 안 함 (기존 사용)" and not server_state.get('has_job_description'):
        st.error("저장된 채용공고가 없습니다. 먼저 채용공고를 입력하세요!")
    elif not uploaded_files and server_state.get('resume_count', 0) == 0:
        st.error("이력서를 업로드하세요!")
    else:
        with st.spinner("AI가 이력서를 분석 중입니다..."):
            try:
                # API 호출 데이터 준비
                files = []
                data = {"top_n": top_n}

                # 이력서 파일 추가
                if uploaded_files:
                    files.extend([("resumes", (f.name, f, f.type)) for f in uploaded_files])

                # 채용공고 데이터 준비
                if jd_file:
                    files.append(("job_description_file", (jd_file.name, jd_file, jd_file.type)))
                elif job_description:
                    data["job_description"] = job_description

                response = httpx.post(
                    f"{API_URL}/screen",
                    files=files if files else None,
                    data=data,
                    timeout=300.0
                )

                if response.status_code == 200:
                    results = response.json()

                    # 정렬 기준에 따라 재정렬
                    candidates = results['top_candidates']
                    if sort_method == "Gemini AI 평가 점수 (100점)":
                        candidates = sorted(candidates, key=lambda x: x['gemini_score'], reverse=True)

                    # 세션에 결과 저장
                    st.session_state['results'] = results
                    st.session_state['candidates'] = candidates
                    st.session_state['sort_method'] = sort_method

                    # 서버 상태 갱신
                    try:
                        state_response = httpx.get(f"{API_URL}/state", timeout=10.0)
                        if state_response.status_code == 200:
                            st.session_state['server_state'] = state_response.json()
                    except:
                        pass

                    st.success(f"✅ {results['total_processed']}명 분석 완료 (소요 시간: {results['processing_time']:.2f}초)")

                    show_results(results, candidates, sort_method)

                else:
                    st.error(f"API 오류: {response.status_code} - {response.text}")

            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)

# 이전 결과가 있으면 표시
elif 'results' in st.session_state:
    results = st.session_state['results']
    candidates = st.session_state['candidates']
    sort_method = st.session_state.get('sort_method', "Jina Reranker 점수 (코사인 유사도)")

    st.info(f"📋 분석 결과: {results['total_processed']}명 분석 완료 (소요 시간: {results['processing_time']:.2f}초)")

    show_results(results, candidates, sort_method)

else:
    # 처음 시작 화면
    st.markdown("---")
    st.markdown("### 👋 시작하기")
    st.markdown("""
    1. **왼쪽 사이드바**에서 채용 공고를 입력하세요
    2. 이력서 파일(PDF/DOCX)을 업로드하세요
    3. **분석 시작** 버튼을 클릭하세요

    💡 **Tip**: 한 번 입력한 채용공고와 이력서는 서버가 재시작되기 전까지 저장됩니다!
    """)

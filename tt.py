import streamlit as st
import re
from hangul_romanize import Transliter
from hangul_romanize.rule import academic
import json
from datetime import datetime
import base64
from collections import defaultdict
from datetime import timedelta
import pandas as pd
import altair as alt

trans = Transliter(academic)

def to_romanized_filename(name):
    try:
        romanized = trans.translit(name)
        romanized = re.sub(r'[^a-zA-Z0-9_]', '', romanized.lower())
        if not romanized:
            romanized = "student"
        return romanized
    except:
        return "student"

# 로고 base64
def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()
    
logo_base64 = image_to_base64("이투스247학원 BI(기본형).png")

# 기본 설정
st.set_page_config(layout="wide")

# ✅ 커스텀 스타일 삽입
st.markdown("""
<style>
    body {
        background-color: #fffffff;
        font-family: 'Segoe UI', 'Pretendard', 'Apple SD Gothic Neo', sans-serif;
        color: #111827;
    }

    .warning-text {
        background-color: #fff4e5;
        padding: 6px 10px;
        border-radius: 8px;
        color: #a14b00;
        font-size: 0.8rem;
        margin-top: 4px;
    }

    .day-header {
        text-align: center;
        font-weight: bold;
        background: #e0f2fe;
        color: #0f172a;
        padding: 8px;
        border-radius: 8px;
        margin-bottom: 12px;
    }

    .class-block {
        padding: 10px;
        text-align: center;
        background-color: #f9f9f9;
        color: #111827;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .stat-card {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 15px;
        background: #d1fae5;
        border-radius: 10px;
        text-align: center;
        height: 100px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);    
    }

    .stat-card h4 {
        font-size: 1.2rem;
        margin: 0;    
    }

    .stat-card p {
        font-size: 1.5rem;
        margin: 0;
    }

    .stat-card:hover {
        transform: scale(1.02);
        transition: all 0.2s ease-in-out;
    }

    .hover-time .minute {
        display: none;
    }

    .hover-time:hover .hour {
        display: none;
    }

    .hover-time:hover .minute {
        display: inline;
    }
    @media (prefers-color-scheme: dark) {

    body {
        background-color: #1e1e1e;
        color: #f9fafb;
        font-family: 'Segoe UI', 'Pretendard', sans-serif;
    }

    /* 입력창 */
    .stTextInput > div {
        border: none !important;
        box-shadow: none !important;
        background: transparent !important;
    }
    .stTextInput > div > div > input {
        background-color: #1f2937 !important;
        color: #f9fafb !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        padding: 0.45rem 0.7rem !important;
        border-radius: 6px !important;
        font-size: 0.9rem;
    }
    .stTextInput input::placeholder {
        color: #9ca3af !important;
    }

    /* 버튼 */
    .stButton button {
        background-color: #3b82f6 !important;
        color: white !important;
        border: none !important;
        box-shadow: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 1rem !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .stButton button:hover {
        background-color: #2563eb !important;
    }

    /* 카드 기본: 밝은 텍스트 */
    .stat-card, .stat-card h4, .stat-card p, .stat-card b {
        color: #111827 !important;
    }
    .class-block {
        background-color: #2b2b2b !important;  /* 어두운 회색 */
        color: #f9fafb !important;  /* 밝은 텍스트 */
        border: 1px solid #3d3d3d;
    }
}
</style>
""", unsafe_allow_html=True)

# 로고 + 타이틀
st.markdown(f"""
<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 20px;">
    <img src="data:image/png;base64,{logo_base64}" alt="logo" style="height: 40px;">
    <h1 style="margin: 0; font-size: 32px;">나만의 시간표</h1>
</div>
""", unsafe_allow_html=True)

# 요일 및 과목
days = ["월", "화", "수", "목", "금", "토", "일"]
subject_options = [ "🟥 국어", "🟧 수학", "🟨 영어", "🟩 물리학","🟩 화학","🟩 생명과학","🟩 지구과학","🟦 생윤/윤사","🟦 사문/정법","🟦 한지/세지","🟦 동사/세사",""]
default_times = [
    "08:00 ~ 10:00", "10:00 ~ 12:00", "13:00 ~ 15:00",
    "15:00 ~ 17:00", "18:00 ~ 20:00", "20:00 ~ 22:00", "22:00 ~ 23:00"
]

이모지_배경색 = {
    "🟥": "#fecaca",  # 국어
    "🟧": "#fed7aa",  # 수학
    "🟨": "#fef9c3",  # 영어
    "🟩": "#86efac",  # 자연탐구
    "🟦": "#bfdbfe",  # 사회탐구
}

# 세션 초기화
if "num_rows" not in st.session_state:
    st.session_state["num_rows"] = len(default_times)
if "time_blocks" not in st.session_state:
    st.session_state["time_blocks"] = default_times.copy()
if "timetable" not in st.session_state:
    st.session_state["timetable"] = {
        f"{i}_{d}": {"subject": "", "teacher": ""}
        for i in range(st.session_state["num_rows"]) for d in days
    }

# 이름 입력
st.sidebar.markdown("### 🧑‍💻 이름 입력")
student_name = st.sidebar.text_input("👤 이름 (저장 및 불러오기용)", key="student_name")

# 교시 추가/삭제
st.sidebar.header("⏰ 시간대 설정")
def add_row():
    st.session_state["num_rows"] += 1
    st.session_state["time_blocks"].append("시간대 입력")
    for d in days:
        st.session_state["timetable"][f"{st.session_state['num_rows']-1}_{d}"] = {"subject": "", "teacher": ""}
def remove_row():
    if st.session_state["num_rows"] > 1:
        st.session_state["num_rows"] -= 1
        st.session_state["time_blocks"].pop()
        for d in days:
            st.session_state["timetable"].pop(f"{st.session_state['num_rows']}_{d}", None)
col1, col2 = st.sidebar.columns(2)
col1.button("➕ 교시 추가", on_click=add_row)
col2.button("➖ 교시 제거", on_click=remove_row)

# 시간대 입력
for i in range(st.session_state["num_rows"]):
    col1, col2 = st.sidebar.columns(2)

    # 교시별 기본 시작 시간 계산 (기준: 08:00 + 2시간 간격)
    default_start_time = (datetime.strptime("08:00", "%H:%M") + timedelta(hours=2*i)).strftime("%H:%M")
    default_end_time = (datetime.strptime(default_start_time, "%H:%M") + timedelta(hours=2)).strftime("%H:%M")

    # 시작 시간 입력
    start_text = col1.text_input(
        f"{i+1}교시 시작",
        value=default_start_time,
        key=f"start_{i}",
        placeholder="예: 08:00"
    )

    # 종료 시간 입력
    end_text = col2.text_input(
        f"{i+1}교시 종료",
        value=default_end_time,
        key=f"end_{i}",
        placeholder="예: 10:00"
    )

    # 유효성 체크 및 저장
    try:
        start_time = datetime.strptime(start_text.strip(), "%H:%M")
        end_time = datetime.strptime(end_text.strip(), "%H:%M")
        st.session_state["time_blocks"][i] = f"{start_time.strftime('%H:%M')} ~ {end_time.strftime('%H:%M')}"
    except:
        st.session_state["time_blocks"][i] = "시간 형식 오류"

# 저장/불러오기
if student_name:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 시간표 저장")
    st.sidebar.download_button(
        label="📥 내 컴퓨터에 저장",
        data=json.dumps({
            "student": student_name,
            "time_blocks": st.session_state["time_blocks"],
            "timetable": st.session_state["timetable"],
            "num_rows": st.session_state["num_rows"]
        }, ensure_ascii=False),
        file_name=f"timetable_{to_romanized_filename(student_name)}.json",
        mime="application/json"
    )

    st.sidebar.markdown("### 📤 시간표 불러오기")
    uploaded_file = st.sidebar.file_uploader("시간표 JSON 파일을 선택하세요 (파일명은 반드시 영문으로 저장)", type="json")

    if uploaded_file:
        # 🔑 파일 이름 검사 먼저
        if not uploaded_file.name.isascii():
            st.sidebar.warning("⚠️ 파일 이름을 영문으로 바꿔서 다시 업로드해 주세요.")
        else:
            try:
                # 이름이 안전할 때만 읽기 시도
                raw = uploaded_file.read().decode("utf-8")
                loaded = json.loads(raw)

                # 값 반영
                st.session_state["time_blocks"] = loaded.get("time_blocks", default_times.copy())
                st.session_state["timetable"] = loaded.get("timetable", {})
                st.session_state["num_rows"] = loaded.get("num_rows", len(st.session_state["time_blocks"]))
                st.sidebar.success(f"✅ '{student_name}'의 시간표 불러오기 완료!")
            except Exception as e:
                st.sidebar.error(f"❌ JSON 파일이 유효하지 않습니다: {e}")
# 시간 계산
left_col, right_col = st.columns([3, 1])
with left_col:
    header = st.columns(len(days) + 1)
    header[0].markdown("")
    for i, day in enumerate(days):
        header[i + 1].markdown(f"<div class='day-header'>{day}</div>", unsafe_allow_html=True)

    for row_idx in range(st.session_state["num_rows"]):
        row = st.columns(len(days) + 1)
        try:
            start_str, end_str = st.session_state["time_blocks"][row_idx].split("~")
            start = datetime.strptime(start_str.strip(), "%H:%M")
            end = datetime.strptime(end_str.strip(), "%H:%M")
            duration = (end - start).seconds // 60
        except:
            duration = 0

        block = f"""
        <div class='class-block'>
            <b>{row_idx+1}교시</b><br>
            <span style='font-size: 0.9rem'>{st.session_state["time_blocks"][row_idx]}</span><br>
            <span style='color: green; font-size: 0.8rem;'>{duration}m</span>
        </div>
        """
        row[0].markdown(block, unsafe_allow_html=True)

        for col_idx, day in enumerate(days):
            key = f"{row_idx}_{day}"

            with row[col_idx + 1]:
                if key == "0_월":
                    default_subject = "🟧 수학"
                else:
                    default_subject = st.session_state["timetable"].get(key, {}).get("subject", "")
                
                subj = st.selectbox(
                    "과목",
                    subject_options,
                    index=subject_options.index(default_subject),
                    key=f"{key}_subject",
                    label_visibility="collapsed"
                )

                # 조건 분기 - 월요일 1교시일 경우에만 placeholder 변경
                if key == "0_월":
                    placeholder_text = "예: 현우진 인강"
                else:
                    placeholder_text = ""

                # 강사 입력 필드
                teacher = st.text_input(
                    "강사",
                    value=st.session_state["timetable"].get(key, {}).get("teacher", ""),
                    key=f"{key}_teacher",
                    label_visibility="collapsed",
                    placeholder=placeholder_text
                )

                st.markdown("</div>", unsafe_allow_html=True)

                if teacher and not any(k in teacher for k in ["단과", "인강", "실모", "자습"]):
                    st.markdown(
                        "<div class='warning-text'>⚠️ 단과 / 인강 / 실모 / 자습 이 포함되지 않으면 통계에 반영되지 않습니다.</div>",
                        unsafe_allow_html=True
                    )

                st.session_state["timetable"][key] = {"subject": subj, "teacher": teacher}

# 통계
탐구_과목 = ["물리학", "화학", "생명과학", "지구과학", "생윤/윤사", "사문/정법", "한지/세지", "동사/세사"]
def 정규화(subject):
    # 이모지 제거
    pure_subject = subject.split(" ")[-1].strip() if subject else ""

    # 탐구 과목 정규화
    return "탐구" if pure_subject in 탐구_과목 else pure_subject

stat_dankwa, stat_ingang, stat_silmo = defaultdict(int), defaultdict(int), defaultdict(int)
순공_by_day = {d: 0 for d in days}
순공_by_subject = defaultdict(int)

for row_idx in range(st.session_state["num_rows"]):
    try:
        start_str, end_str = st.session_state["time_blocks"][row_idx].split("~")
        start = datetime.strptime(start_str.strip(), "%H:%M")
        end = datetime.strptime(end_str.strip(), "%H:%M")
        duration = (end - start).seconds // 60
    except:
        duration = 0

    for day in days:
        key = f"{row_idx}_{day}"
        cell = st.session_state["timetable"].get(key, {})
        subj = 정규화(cell.get("subject", "").strip())
        teacher = cell.get("teacher", "").strip().lower()
        if not subj or not teacher:
            continue
        if "단과" in teacher:
            stat_dankwa[subj] += duration
        elif "인강" in teacher:
            stat_ingang[subj] += duration
        elif "실모" in teacher:
            stat_silmo[subj] += duration
        else:
            순공_by_day[day] += duration
            순공_by_subject[subj] += duration

순공_total = sum(순공_by_day.values())

with right_col:
    def render_card(title, data):
        total = sum(data.values())
        total_h = total // 60
        total_m = total % 60
        st.markdown(f"""
            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'>
                <h4 style='margin: 0;'>{title}</h4>
                <span style='font-weight: bold; color: #1e3a8a;'>
                    <span style='font-size: 28px;'>{total_h}</span>
                    <span style='font-size: 14px;'>시간 </span>
                    <span style='font-size: 28px;'>{total_m}</span>
                    <span style='font-size: 14px;'>분</span>
                </span>
            </div>
            """, unsafe_allow_html=True)
        

        row = st.columns(4)
        for i, subj in enumerate(["국어", "수학", "영어", "탐구"]):
            value = data.get(subj, 0)
            full_name = [s for s in subject_options if s.endswith(subj)]
            emoji = full_name[0].split(" ")[0] if full_name else ""
            if subj == "탐구":
                emoji = "🟦"
            bg_color = 이모지_배경색.get(emoji, "#e0f7fa")

            with row[i]:
                st.markdown(f"""
                    <div class='stat-card' style='background: {bg_color};'>
                        <h4>{subj}</h4>
                        <p>
                            <span class="hover-time">
                                <span class="hour"><b>{value // 60}</b></span>
                                <span class="minute"><b>{value}</b></span>
                            </span>
                        </p>
                    </div>
                """, unsafe_allow_html=True)


    # 순공 총합 출력 수정
    순공_total_h = 순공_total // 60
    순공_total_m = 순공_total % 60

    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    render_card("주간 단과 시간", stat_dankwa)
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    render_card("주간 인강 시간", stat_ingang)
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    render_card("주간 실모 시간", stat_silmo)
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;'>
        <h4 style='margin: 0;'>최대 순공 시간</h4>
        <span style='font-weight: bold; color: #1e3a8a;'>
            <span style='font-size: 28px;'>{순공_total_h}</span>
            <span style='font-size: 14px;'>시간 </span>
            <span style='font-size: 28px;'>{순공_total_m}</span>
            <span style='font-size: 14px;'>분</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # 요일별 카드
    row1 = st.columns(4)
    for i, day in enumerate(["월", "화", "수", "목"]):
        mins = 순공_by_day.get(day, 0)
        with row1[i]:
            st.markdown(f"""
                <div class='stat-card'>
                    <h4>{day}</h4>
                    <p class="hover-time">
                        <span class="hour"><b>{mins // 60}</b></span>
                        <span class="minute"><b>{mins}</b></span>
                    </p>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    row2 = st.columns(4)
    for i, day in enumerate(["금", "토", "일", "합계"]):
        mins = 순공_total if day == "합계" else 순공_by_day.get(day, 0)
        with row2[i]:
            st.markdown(f"""
                <div class='stat-card'>
                    <h4>{day}</h4>
                    <p class="hover-time">
                        <span class="hour"><b>{mins // 60}</b></span>
                        <span class="minute"><b>{mins}</b></span>
                    </p>
                </div>
            """, unsafe_allow_html=True)

st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

# 📊 공통 데이터 구성
total_data = {
    "단과": sum(stat_dankwa.values()),
    "인강": sum(stat_ingang.values()),
    "실모": sum(stat_silmo.values()),
    "순공": 순공_total
}
df_pie = pd.DataFrame({"유형": total_data.keys(), "시간(분)": total_data.values()})

df_day = pd.DataFrame({
    "요일": list(순공_by_day.keys()),
    "시간(분)": list(순공_by_day.values())
})

subject_set = set(stat_dankwa.keys()) | set(stat_ingang.keys()) | set(stat_silmo.keys())
data_subject = []
for subj in subject_set:
    data_subject.append({"과목": subj, "유형": "단과", "시간": stat_dankwa.get(subj, 0)})
    data_subject.append({"과목": subj, "유형": "인강", "시간": stat_ingang.get(subj, 0)})
    data_subject.append({"과목": subj, "유형": "실모", "시간": stat_silmo.get(subj, 0)})
for subj, time in 순공_by_subject.items():
    data_subject.append({"과목": subj, "유형": "순공", "시간": time})
df_subj = pd.DataFrame(data_subject)

# 🎨 컬러 지정
color_map = {
    "단과": "#f87171",  # 빨간계열
    "인강": "#60a5fa",  # 파란계열
    "실모": "#34d399",  # 초록계열
    "순공": "#fbbf24"   # 노란계열
}
요일색 = {
    "월": "#e0f2fe", "화": "#bae6fd", "수": "#7dd3fc", "목": "#38bdf8",
    "금": "#0ea5e9", "토": "#0284c7", "일": "#0369a1"
}

# 🔳 레이아웃 나누기
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🧩 학습 유형별 비율")
    pie_chart = alt.Chart(df_pie).mark_arc(innerRadius=50).encode(
        theta="시간(분):Q",
        color=alt.Color(
            "유형:N",
            scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
            legend=alt.Legend(orient="bottom")
        ),
        tooltip=["유형:N", "시간(분):Q"]
    ).properties(width=260, height=260)
    st.altair_chart(pie_chart, use_container_width=True)

with col2:
    st.markdown("### 📅 요일별 순공 시간")
    bar_chart_day = alt.Chart(df_day).mark_bar().encode(
        x=alt.X("요일:N", sort=days),
        y="시간(분):Q",
        color=alt.Color(
            "요일:N",
            scale=alt.Scale(domain=list(요일색.keys()), range=list(요일색.values())),
            legend=alt.Legend(orient="bottom")
        ),
        tooltip=["요일:N", "시간(분):Q"]
    ).properties(height=260)
    st.altair_chart(bar_chart_day, use_container_width=True)

with col3:
    st.markdown("### 📚 과목별 누적 시간")
    bar_chart_subj = alt.Chart(df_subj).mark_bar().encode(
        x="과목:N",
        y="시간:Q",
        color=alt.Color(
            "유형:N",
            scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())),
            legend=alt.Legend(orient="bottom")
        ),
        tooltip=["과목:N", "유형:N", "시간:Q"]
    ).properties(height=260)
    st.altair_chart(bar_chart_subj, use_container_width=True)

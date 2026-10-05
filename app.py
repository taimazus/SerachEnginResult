import streamlit as st

from rank_checker import RankCheckError, check_google_rank
from storage import (
    add_keyword,
    create_project,
    get_history,
    get_keywords,
    get_projects,
    initialize_database,
    save_check,
)


st.set_page_config(page_title="Local Rank Tracker", page_icon="🔎", layout="wide")
initialize_database()

st.markdown(
    """
    <style>
    @font-face {
        font-family: "Vazirmatn";
        src: url("/app/static/Vazirmatn.woff2") format("woff2");
        font-style: normal;
        font-weight: 100 900;
        font-display: swap;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: "Vazirmatn", sans-serif !important;
    }
    h1, h2, h3, p, label, input, textarea, button,
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
    [data-testid="stCaptionContainer"], [data-testid="stAlert"] {
        font-family: "Vazirmatn", sans-serif !important;
    }
    [data-testid="stMainBlockContainer"], [data-testid="stSidebar"] {
        direction: rtl;
        text-align: right;
    }
    [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
    [data-testid="stCaptionContainer"], [data-testid="stAlert"] {
        direction: rtl;
        text-align: right;
        font-family: "Vazirmatn", sans-serif;
    }
    button, input, textarea, [data-baseweb="select"] {
        font-family: "Vazirmatn", sans-serif;
    }
    .st-key-target_domain input {
        direction: ltr;
        text-align: left;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("بررسی محلی رتبهٔ جست‌وجو")
st.caption(
    "هر بررسی فقط با اقدام شما اجرا می‌شود. جست‌وجو محدود است؛ در صورت CAPTCHA "
    "بررسی متوقف می‌شود و هیچ تلاشی برای دور زدن آن انجام نمی‌شود."
)

with st.expander("ساخت پروژه"):
    with st.form("create_project", clear_on_submit=True):
        project_name = st.text_input("نام پروژه")
        create_submitted = st.form_submit_button("ایجاد پروژه")
    if create_submitted:
        try:
            create_project(project_name)
            st.success("پروژه ایجاد شد.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

projects = get_projects()
if not projects:
    st.info("برای شروع، یک پروژه ایجاد کنید.")
    st.stop()

project_by_name = {project["name"]: project for project in projects}
selected_name = st.selectbox("پروژه", list(project_by_name))
selected_project = project_by_name[selected_name]

with st.expander("افزودن عبارت جست‌وجو"):
    with st.form("add_keyword", clear_on_submit=True):
        query = st.text_input(
            "عبارت جست‌وجو",
            placeholder="مثلاً تعمیر تلویزیون در تبریز",
            key="search_query",
        )
        domain = st.text_input(
            "دامنهٔ هدف", placeholder="example.ir", key="target_domain"
        )
        add_submitted = st.form_submit_button("افزودن")
    if add_submitted:
        try:
            add_keyword(selected_project["id"], query, domain)
            st.success("عبارت به پروژه اضافه شد.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))

keywords = get_keywords(selected_project["id"])
if not keywords:
    st.info("هنوز عبارتی برای این پروژه ثبت نشده است.")
    st.stop()

st.subheader("عبارت‌های پیگیری‌شده")
for keyword in keywords:
    with st.container(border=True):
        left, right = st.columns([4, 1])
        with left:
            st.markdown(f"**{keyword['query']}**")
            st.caption(keyword["target_domain"])
        with right:
            if st.button("بررسی رتبه", key=f"check_{keyword['id']}"):
                with st.spinner("در حال بررسی محدود نتایج Google…"):
                    try:
                        result = check_google_rank(
                            keyword["query"], keyword["target_domain"]
                        )
                    except RankCheckError as error:
                        result = {
                            "status": "error",
                            "rank": None,
                            "result_page": None,
                            "message": str(error),
                        }
                    save_check(keyword["id"], result)
                    if result["status"] == "captcha":
                        st.warning(result["message"])
                    elif result["status"] == "error":
                        st.error(result["message"])
                    elif result["status"] == "found":
                        st.success(
                            f"رتبهٔ {result['rank']}، صفحهٔ {result['result_page']}"
                        )
                    else:
                        st.info(result["message"])

        history = get_history(keyword["id"], limit=5)
        if history:
            st.caption("آخرین بررسی‌ها")
            for check in history:
                if check["status"] == "found":
                    rank_text = (
                        f"رتبهٔ {check['rank']} (صفحهٔ {check['result_page']})"
                    )
                elif check["status"] == "error" and (
                    "Executable doesn't exist" in check["message"]
                    or "Playwright was just installed" in check["message"]
                ):
                    rank_text = (
                        "اجرای قبلی به‌دلیل آماده‌نبودن مرورگر ناموفق شد؛ "
                        "اکنون دوباره بررسی کنید."
                    )
                elif check["status"] == "error":
                    rank_text = check["message"][:240]
                    if len(check["message"]) > 240:
                        rank_text += "…"
                else:
                    rank_text = check["message"]
                st.write(f"{check['checked_at']} · {rank_text}")

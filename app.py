import csv
from datetime import datetime
from pathlib import Path
from statistics import mean

import streamlit as st


st.set_page_config(
    page_title="VND → AUD Transfer Optimiser",
    page_icon="💱",
    layout="wide",
)

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        .hero {
            background: linear-gradient(125deg, #0b5d57 0%, #0f766e 55%, #0891b2 100%);
            border-radius: 22px;
            color: white;
            padding: 2.2rem 2.4rem;
            margin-bottom: 1.4rem;
            box-shadow: 0 14px 35px rgba(15, 118, 110, 0.18);
        }
        .hero h1 {
            color: white;
            font-size: clamp(2rem, 4vw, 3.25rem);
            line-height: 1.08;
            margin: 0 0 0.65rem 0;
        }
        .hero p {
            color: rgba(255, 255, 255, 0.88);
            font-size: 1.05rem;
            margin: 0;
            max-width: 760px;
        }
        .eyebrow {
            color: #99f6e4;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            margin-bottom: 0.65rem;
            text-transform: uppercase;
        }
        [data-testid="stMetric"] {
            border-radius: 14px;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.18);
        }
    </style>
    """,
    unsafe_allow_html=True,
)


translations = {
    "English": {
        "sidebar_settings": "Transfer settings",
        "aud_amount": "AUD amount to transfer",
        "deadline": "Days until transfer deadline",
        "set_budget": "Set a maximum VND budget",
        "maximum_budget": "Maximum VND budget",
        "data_caption": "Data source: Vietcombank AUD selling-rate history",
        "data_error": "At least 31 valid rate records are required.",
        "eyebrow": "Exchange-rate decision dashboard",
        "title": "VND → AUD Transfer Optimiser",
        "subtitle": "Historical context, budget planning and a transparent short-term forecast in one place.",
        "updated": "Updated",
        "lower_better": "Lower is better when buying AUD with VND.",
        "tab_overview": "Overview",
        "tab_planner": "Transfer planner",
        "tab_forecast": "Analysis & forecast",
        "current_rate": "Current rate",
        "vs_previous": "vs previous record",
        "vs_7": "Vs 7-day average",
        "vs_30": "Vs 30-day average",
        "range_30": "30-day range",
        "market_read": "Market read",
        "favourable": "Relatively favourable",
        "favourable_text": "The current rate is below both recent averages. AUD is relatively cheaper than its recent trend.",
        "expensive": "Relatively expensive",
        "expensive_text": "The current rate is above both recent averages. AUD is relatively more expensive than its recent trend.",
        "mixed": "Mixed conditions",
        "mixed_text": "The 7-day and 30-day signals disagree, so the recent trend is not decisive.",
        "percentile_text": "Today's rate is better than **{all_value:.0f}%** of earlier recorded rates and **{recent_value:.0f}%** of the previous 90 records.",
        "history": "Rate history",
        "history_help": "A falling line is favourable because fewer VND are needed for each AUD.",
        "window": "History window",
        "window_30": "30 records",
        "window_90": "90 records",
        "window_all": "All data",
        "chart_rate": "VND per AUD",
        "planner_title": "Plan your transfer",
        "planner_intro": "Use the current rate to estimate cost, compare it with recent history and test an optional budget.",
        "current_cost": "Current transfer cost",
        "aud_received": "AUD received",
        "average_cost": "At 30-day average",
        "difference": "Difference",
        "vnd_calculator": "Quick VND → AUD calculator",
        "vnd_amount": "VND amount available",
        "estimated_receive": "Estimated amount received",
        "cost_less": "Today's transfer would cost approximately **{value:,.0f} VND less** than at the previous 30-day average.",
        "cost_more": "Today's transfer would cost approximately **{value:,.0f} VND more** than at the previous 30-day average.",
        "maximum_rate": "Maximum affordable rate",
        "within_budget": "Within budget by **{value:,.0f} VND**.",
        "over_budget": "Over budget by **{value:,.0f} VND**.",
        "no_budget": "No maximum budget is set. Turn it on in the sidebar to test a spending limit.",
        "deadline_warning": "Your deadline is close. Historical testing found no reliable advantage from waiting.",
        "forecast_title": "Short-term rate outlook",
        "forecast_intro": "The most reliable tested one-step baseline is the latest observed rate. The range below applies historical one-record movements to that baseline.",
        "point_forecast": "Next-record estimate",
        "forecast_cost": "Estimated transfer cost",
        "historical_range": "80% historical range",
        "baseline_mae": "Baseline MAE",
        "range_caption": "Historical movement range: **{low:,.2f}–{high:,.2f} VND/AUD**, based on the middle 80% of the latest {count} one-record changes.",
        "direction_title": "Recent direction profile",
        "lower_next": "Lower",
        "unchanged_next": "Unchanged",
        "higher_next": "Higher",
        "direction_caption": "Share of the latest {count} recorded changes. Lower is favourable for buying AUD.",
        "trend_title": "Trend and risk indicators",
        "average_move": "Average daily move (30)",
        "best_30": "Best rate (30)",
        "worst_30": "Worst rate (30)",
        "spread_30": "30-record spread",
        "forecast_note": "Forecasts are uncertain. This baseline previously achieved a mean absolute error of about {mae:,.2f} VND/AUD, while more complex regression and timing models performed worse and were discarded.",
        "evaluation": "Model evaluation details",
        "naive_result": "Naive one-step forecast MAE: **{mae:,.2f} VND/AUD** across {count} historical predictions.",
        "regression_result": "Walk-forward regression MAE: **56.51 VND**, compared with **53.06 VND** for its baseline test. The regression model was discarded.",
        "strategy_result": "The tested 14-day timing strategy was **5.79 VND/AUD worse** than transferring immediately on average, so it was discarded.",
        "disclaimer": "Educational decision support only — not financial advice or a guaranteed forecast. Transfer fees and provider spreads are not included.",
    },
    "Tiếng Việt": {
        "sidebar_settings": "Thiết lập chuyển tiền",
        "aud_amount": "Số AUD cần chuyển",
        "deadline": "Số ngày còn lại đến hạn chuyển",
        "set_budget": "Đặt ngân sách VND tối đa",
        "maximum_budget": "Ngân sách VND tối đa",
        "data_caption": "Nguồn dữ liệu: lịch sử tỷ giá bán AUD của Vietcombank",
        "data_error": "Cần ít nhất 31 bản ghi tỷ giá hợp lệ.",
        "eyebrow": "Bảng hỗ trợ quyết định tỷ giá",
        "title": "Công cụ tối ưu chuyển tiền VND → AUD",
        "subtitle": "Bối cảnh lịch sử, lập ngân sách và dự báo ngắn hạn minh bạch trong cùng một nơi.",
        "updated": "Cập nhật",
        "lower_better": "Tỷ giá càng thấp càng có lợi khi mua AUD bằng VND.",
        "tab_overview": "Tổng quan",
        "tab_planner": "Lập kế hoạch",
        "tab_forecast": "Phân tích & dự báo",
        "current_rate": "Tỷ giá hiện tại",
        "vs_previous": "so với bản ghi trước",
        "vs_7": "So với TB 7 ngày",
        "vs_30": "So với TB 30 ngày",
        "range_30": "Khoảng 30 ngày",
        "market_read": "Nhận định thị trường",
        "favourable": "Tương đối thuận lợi",
        "favourable_text": "Tỷ giá hiện tại thấp hơn cả hai mức trung bình gần đây. AUD đang tương đối rẻ hơn xu hướng gần đây.",
        "expensive": "Tương đối đắt",
        "expensive_text": "Tỷ giá hiện tại cao hơn cả hai mức trung bình gần đây. AUD đang tương đối đắt hơn xu hướng gần đây.",
        "mixed": "Tín hiệu trái chiều",
        "mixed_text": "Tín hiệu 7 ngày và 30 ngày không đồng thuận, vì vậy xu hướng gần đây chưa rõ ràng.",
        "percentile_text": "Tỷ giá hôm nay tốt hơn **{all_value:.0f}%** các tỷ giá đã ghi nhận trước đây và **{recent_value:.0f}%** trong 90 bản ghi gần nhất.",
        "history": "Lịch sử tỷ giá",
        "history_help": "Đường đi xuống là thuận lợi vì cần ít VND hơn cho mỗi AUD.",
        "window": "Khoảng thời gian",
        "window_30": "30 bản ghi",
        "window_90": "90 bản ghi",
        "window_all": "Toàn bộ dữ liệu",
        "chart_rate": "VND trên mỗi AUD",
        "planner_title": "Lập kế hoạch chuyển tiền",
        "planner_intro": "Dùng tỷ giá hiện tại để ước tính chi phí, so sánh với lịch sử gần đây và kiểm tra ngân sách tùy chọn.",
        "current_cost": "Chi phí chuyển hiện tại",
        "aud_received": "AUD nhận được",
        "average_cost": "Theo TB 30 ngày",
        "difference": "Chênh lệch",
        "vnd_calculator": "Quy đổi nhanh VND → AUD",
        "vnd_amount": "Số VND hiện có",
        "estimated_receive": "Số tiền ước tính nhận được",
        "cost_less": "Chuyển hôm nay sẽ rẻ hơn khoảng **{value:,.0f} VND** so với mức trung bình 30 ngày trước.",
        "cost_more": "Chuyển hôm nay sẽ đắt hơn khoảng **{value:,.0f} VND** so với mức trung bình 30 ngày trước.",
        "maximum_rate": "Tỷ giá tối đa có thể chi trả",
        "within_budget": "Thấp hơn ngân sách **{value:,.0f} VND**.",
        "over_budget": "Vượt ngân sách **{value:,.0f} VND**.",
        "no_budget": "Chưa đặt ngân sách tối đa. Bật tùy chọn trong thanh bên để kiểm tra giới hạn chi tiêu.",
        "deadline_warning": "Thời hạn chuyển tiền đã gần. Kiểm tra lịch sử không cho thấy chờ đợi mang lại lợi thế đáng tin cậy.",
        "forecast_title": "Triển vọng tỷ giá ngắn hạn",
        "forecast_intro": "Mô hình cơ sở một bước đáng tin cậy nhất đã kiểm tra dùng tỷ giá mới nhất. Khoảng dưới đây áp dụng biến động lịch sử của một bản ghi vào mức cơ sở đó.",
        "point_forecast": "Ước tính bản ghi tiếp theo",
        "forecast_cost": "Chi phí chuyển ước tính",
        "historical_range": "Khoảng lịch sử 80%",
        "baseline_mae": "MAE mô hình cơ sở",
        "range_caption": "Khoảng biến động lịch sử: **{low:,.2f}–{high:,.2f} VND/AUD**, dựa trên 80% biến động trung tâm của {count} thay đổi gần nhất.",
        "direction_title": "Phân bố hướng biến động gần đây",
        "lower_next": "Giảm",
        "unchanged_next": "Không đổi",
        "higher_next": "Tăng",
        "direction_caption": "Tỷ trọng trong {count} thay đổi gần nhất. Giảm là có lợi khi mua AUD.",
        "trend_title": "Chỉ báo xu hướng và rủi ro",
        "average_move": "Biến động TB mỗi ngày (30)",
        "best_30": "Tỷ giá tốt nhất (30)",
        "worst_30": "Tỷ giá xấu nhất (30)",
        "spread_30": "Biên độ 30 bản ghi",
        "forecast_note": "Dự báo luôn có độ bất định. Mô hình cơ sở này trước đây có sai số tuyệt đối trung bình khoảng {mae:,.2f} VND/AUD; các mô hình hồi quy và chọn thời điểm phức tạp hơn cho kết quả kém hơn nên đã bị loại.",
        "evaluation": "Chi tiết đánh giá mô hình",
        "naive_result": "MAE dự báo một bước đơn giản: **{mae:,.2f} VND/AUD** trên {count} dự báo lịch sử.",
        "regression_result": "MAE hồi quy cuốn chiếu là **56.51 VND**, so với **53.06 VND** của mô hình cơ sở trong cùng bài kiểm tra. Mô hình hồi quy đã bị loại.",
        "strategy_result": "Chiến lược chọn thời điểm trong 14 ngày tệ hơn trung bình **5.79 VND/AUD** so với chuyển ngay, nên đã bị loại.",
        "disclaimer": "Chỉ nhằm hỗ trợ quyết định và mục đích giáo dục — không phải tư vấn tài chính hay dự báo được bảo đảm. Chưa bao gồm phí chuyển và chênh lệch giá của nhà cung cấp.",
    },
}


def percentile(values, fraction):
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = position - lower_index
    return (
        ordered[lower_index] * (1 - weight)
        + ordered[upper_index] * weight
    )


language = st.sidebar.selectbox(
    "Language / Ngôn ngữ",
    ("English", "Tiếng Việt"),
    key="language",
)
t = translations[language]

st.sidebar.markdown(f"### {t['sidebar_settings']}")
aud_amount = st.sidebar.number_input(
    t["aud_amount"],
    min_value=1.0,
    value=3000.0,
    step=100.0,
    key="aud_amount",
)
days_remaining = st.sidebar.number_input(
    t["deadline"],
    min_value=0,
    value=14,
    step=1,
    key="days_remaining",
)
use_budget = st.sidebar.checkbox(t["set_budget"], key="use_budget")
maximum_budget_vnd = None
if use_budget:
    maximum_budget_vnd = st.sidebar.number_input(
        t["maximum_budget"],
        min_value=1_000_000,
        value=57_000_000,
        step=100_000,
        key="maximum_budget_vnd",
    )
st.sidebar.divider()
st.sidebar.caption(t["data_caption"])

data_file = Path(__file__).parent / "data" / "vcb_aud_daily.csv"
with data_file.open(newline="", encoding="utf-8") as file:
    rows = [
        row
        for row in csv.DictReader(file)
        if row.get("date") and row.get("sell")
    ]

rows.sort(key=lambda row: row["date"])
if len(rows) < 31:
    st.error(t["data_error"])
    st.stop()

dates = [datetime.fromisoformat(row["date"]) for row in rows]
date_labels = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]
latest = rates[-1]
previous = rates[-2]
previous_30_rates = rates[-31:-1]
average_7 = mean(previous_30_rates[-7:])
average_30 = mean(previous_30_rates)
latest_30 = rates[-30:]
daily_changes = [
    current - prior
    for prior, current in zip(rates, rates[1:])
]
baseline_mae = mean(abs(change) for change in daily_changes)
recent_change_window = daily_changes[-180:]
range_low = latest + percentile(recent_change_window, 0.10)
range_high = latest + percentile(recent_change_window, 0.90)
average_move_30 = mean(abs(change) for change in daily_changes[-30:])

historical_rates = rates[:-1]
better_than = sum(rate > latest for rate in historical_rates)
all_percentile = better_than / len(historical_rates) * 100
recent_rates = rates[-91:-1]
better_recent = sum(rate > latest for rate in recent_rates)
recent_percentile = better_recent / len(recent_rates) * 100

lower_count = sum(change < 0 for change in recent_change_window)
unchanged_count = sum(change == 0 for change in recent_change_window)
higher_count = sum(change > 0 for change in recent_change_window)
direction_count = len(recent_change_window)

current_cost = aud_amount * latest
average_30_cost = aud_amount * average_30
average_cost_difference = average_30_cost - current_cost
forecast_cost = aud_amount * latest

st.markdown(
    f"""
    <div class="hero">
        <div class="eyebrow">{t["eyebrow"]}</div>
        <h1>{t["title"]}</h1>
        <p>{t["subtitle"]}</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.caption(f"{t['updated']}: {date_labels[-1]} · {t['lower_better']}")

overview_tab, planner_tab, forecast_tab = st.tabs(
    [
        f"📊 {t['tab_overview']}",
        f"🧮 {t['tab_planner']}",
        f"🔎 {t['tab_forecast']}",
    ]
)

with overview_tab:
    metric_1, metric_2, metric_3, metric_4 = st.columns(4)
    metric_1.metric(
        t["current_rate"],
        f"{latest:,.2f}",
        delta=f"{latest - previous:+,.2f} {t['vs_previous']}",
        delta_color="inverse",
        border=True,
    )
    metric_2.metric(
        t["vs_7"],
        f"{latest - average_7:+,.2f}",
        delta=f"{(latest / average_7 - 1) * 100:+.2f}%",
        delta_color="inverse",
        border=True,
    )
    metric_3.metric(
        t["vs_30"],
        f"{latest - average_30:+,.2f}",
        delta=f"{(latest / average_30 - 1) * 100:+.2f}%",
        delta_color="inverse",
        border=True,
    )
    metric_4.metric(
        t["range_30"],
        f"{min(latest_30):,.0f}–{max(latest_30):,.0f}",
        delta=f"{max(latest_30) - min(latest_30):,.0f} VND",
        delta_color="off",
        border=True,
    )

    st.subheader(t["market_read"])
    if latest < average_7 and latest < average_30:
        st.success(f"**{t['favourable']}** — {t['favourable_text']}")
    elif latest > average_7 and latest > average_30:
        st.warning(f"**{t['expensive']}** — {t['expensive_text']}")
    else:
        st.info(f"**{t['mixed']}** — {t['mixed_text']}")
    st.write(
        t["percentile_text"].format(
            all_value=all_percentile,
            recent_value=recent_percentile,
        )
    )

    chart_header, window_column = st.columns([3, 1])
    with chart_header:
        st.subheader(t["history"])
        st.caption(t["history_help"])
    with window_column:
        history_window = st.selectbox(
            t["window"],
            (30, 90, 0),
            index=1,
            format_func=lambda value: {
                30: t["window_30"],
                90: t["window_90"],
                0: t["window_all"],
            }[value],
            key="history_window",
        )

    if history_window == 30:
        start_index = -30
    elif history_window == 90:
        start_index = -90
    else:
        start_index = 0

    chart_rate_label = t["chart_rate"]
    chart_data = {
        "date": dates[start_index:],
        chart_rate_label: rates[start_index:],
    }
    st.line_chart(
        chart_data,
        x="date",
        y=chart_rate_label,
        height=400,
    )

with planner_tab:
    st.subheader(t["planner_title"])
    st.write(t["planner_intro"])

    plan_1, plan_2, plan_3, plan_4 = st.columns(4)
    plan_1.metric(
        t["current_cost"],
        f"{current_cost:,.0f} VND",
        border=True,
    )
    plan_2.metric(
        t["aud_received"],
        f"AUD {aud_amount:,.2f}",
        border=True,
    )
    plan_3.metric(
        t["average_cost"],
        f"{average_30_cost:,.0f} VND",
        border=True,
    )
    plan_4.metric(
        t["difference"],
        f"{abs(average_cost_difference):,.0f} VND",
        delta=f"{average_cost_difference:+,.0f} VND",
        delta_color="normal",
        border=True,
    )

    if average_cost_difference >= 0:
        st.success(t["cost_less"].format(value=average_cost_difference))
    else:
        st.warning(
            t["cost_more"].format(
                value=abs(average_cost_difference)
            )
        )

    if maximum_budget_vnd is not None:
        maximum_affordable_rate = maximum_budget_vnd / aud_amount
        budget_difference = maximum_budget_vnd - current_cost
        st.write(
            f"{t['maximum_rate']}: "
            f"**{maximum_affordable_rate:,.2f} VND/AUD**"
        )
        if budget_difference >= 0:
            st.success(t["within_budget"].format(value=budget_difference))
        else:
            st.error(
                t["over_budget"].format(
                    value=abs(budget_difference)
                )
            )
    else:
        st.info(t["no_budget"])

    if days_remaining <= 2:
        st.warning(t["deadline_warning"])

    st.divider()
    calculator_1, calculator_2 = st.columns([2, 1])
    with calculator_1:
        st.subheader(t["vnd_calculator"])
        vnd_amount = st.number_input(
            t["vnd_amount"],
            min_value=1_000_000,
            value=56_000_000,
            step=1_000_000,
            key="vnd_amount",
        )
    with calculator_2:
        st.metric(
            t["estimated_receive"],
            f"AUD {vnd_amount / latest:,.2f}",
            border=True,
        )

with forecast_tab:
    st.subheader(t["forecast_title"])
    st.write(t["forecast_intro"])

    forecast_1, forecast_2, forecast_3, forecast_4 = st.columns(4)
    forecast_1.metric(
        t["point_forecast"],
        f"{latest:,.2f} VND/AUD",
        border=True,
    )
    forecast_2.metric(
        t["forecast_cost"],
        f"{forecast_cost:,.0f} VND",
        border=True,
    )
    forecast_3.metric(
        t["historical_range"],
        f"{range_low:,.0f}–{range_high:,.0f}",
        border=True,
    )
    forecast_4.metric(
        t["baseline_mae"],
        f"{baseline_mae:,.2f} VND/AUD",
        border=True,
    )
    st.caption(
        t["range_caption"].format(
            low=range_low,
            high=range_high,
            count=len(recent_change_window),
        )
    )

    st.subheader(t["direction_title"])
    direction_1, direction_2, direction_3 = st.columns(3)
    direction_1.metric(
        t["lower_next"],
        f"{lower_count / direction_count * 100:.1f}%",
        border=True,
    )
    direction_2.metric(
        t["unchanged_next"],
        f"{unchanged_count / direction_count * 100:.1f}%",
        border=True,
    )
    direction_3.metric(
        t["higher_next"],
        f"{higher_count / direction_count * 100:.1f}%",
        border=True,
    )
    st.caption(t["direction_caption"].format(count=direction_count))

    st.subheader(t["trend_title"])
    trend_1, trend_2, trend_3, trend_4 = st.columns(4)
    trend_1.metric(
        t["average_move"],
        f"{average_move_30:,.2f} VND",
        border=True,
    )
    trend_2.metric(
        t["best_30"],
        f"{min(latest_30):,.2f}",
        border=True,
    )
    trend_3.metric(
        t["worst_30"],
        f"{max(latest_30):,.2f}",
        border=True,
    )
    trend_4.metric(
        t["spread_30"],
        f"{max(latest_30) - min(latest_30):,.2f}",
        border=True,
    )

    st.info(t["forecast_note"].format(mae=baseline_mae))
    with st.expander(t["evaluation"]):
        st.write(
            t["naive_result"].format(
                mae=baseline_mae,
                count=len(daily_changes),
            )
        )
        st.write(t["regression_result"])
        st.write(t["strategy_result"])

st.divider()
st.caption(t["disclaimer"])

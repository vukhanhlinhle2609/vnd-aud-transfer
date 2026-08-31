import csv
from pathlib import Path
from statistics import mean

import streamlit as st


st.set_page_config(
    page_title="VND → AUD Transfer Optimiser",
    page_icon="💱",
)

language = st.sidebar.selectbox(
    "Language / Ngôn ngữ",
    ("English", "Tiếng Việt"),
)

translations = {
    "English": {
        "data_error": "At least 31 days of rate data are required.",
        "title": "VND → AUD Transfer Optimiser",
        "rate_label": "Vietcombank AUD selling rate",
        "vs_yesterday": "vs yesterday",
        "last_updated": "Last updated",
        "lower_is_better": "A lower VND-per-AUD rate is better.",
        "how_good": "How good is today?",
        "earlier_days": "Today's rate is better than **{value:.0f}%** of earlier recorded days.",
        "recent_days": "Better than **{value:.0f}%** of the previous 90 days.",
        "average_7": "Previous 7-day average: **{value:,.2f} VND/AUD**",
        "average_30": "Previous 30-day average: **{value:,.2f} VND/AUD**",
        "history": "Rate history",
        "chart_rate": "VND per AUD",
        "calculator": "VND to AUD calculator",
        "vnd_amount": "VND amount",
        "amount_received": "Estimated amount received: **A${value:,.2f}**",
        "planner": "Transfer budget planner",
        "aud_amount": "AUD amount to transfer",
        "deadline": "Days until the transfer deadline",
        "set_budget": "Set a maximum VND budget",
        "maximum_budget": "Maximum VND budget",
        "current_cost": "Current cost for {amount:,.2f} AUD: **{cost:,.0f} VND**",
        "cost_less": "Today costs approximately {value:,.0f} VND less than the previous 30-day average.",
        "cost_more": "Today costs approximately {value:,.0f} VND more than the previous 30-day average.",
        "maximum_rate": "Maximum affordable rate: **{value:,.2f} VND/AUD**",
        "within_budget": "Within budget by {value:,.0f} VND.",
        "over_budget": "Over budget by {value:,.0f} VND.",
        "no_budget": "No maximum budget has been provided.",
        "close_deadline": "Your deadline is close. Historical testing found no reliable advantage from waiting.",
        "no_edge": "No validated timing edge has been found. This dashboard provides historical context and budget calculations, not a guaranteed forecast.",
        "model_results": "Model evaluation results",
        "naive_result": "Naive one-day forecast MAE: **47.59 VND per AUD**.",
        "regression_result": "Walk-forward regression MAE: **56.51 VND**, compared with **53.06 VND** for the baseline. The regression model was discarded.",
        "strategy_result": "The tested 14-day timing strategy was **5.79 VND per AUD worse** than transferring immediately on average, so it was discarded.",
    },
    "Tiếng Việt": {
        "data_error": "Cần ít nhất 31 ngày dữ liệu tỷ giá.",
        "title": "Công cụ tối ưu chuyển tiền VND → AUD",
        "rate_label": "Tỷ giá bán AUD của Vietcombank",
        "vs_yesterday": "so với hôm qua",
        "last_updated": "Cập nhật lần cuối",
        "lower_is_better": "Tỷ giá VND trên mỗi AUD càng thấp thì càng có lợi.",
        "how_good": "Tỷ giá hôm nay tốt đến mức nào?",
        "earlier_days": "Tỷ giá hôm nay tốt hơn **{value:.0f}%** số ngày đã ghi nhận trước đây.",
        "recent_days": "Tốt hơn **{value:.0f}%** số ngày trong 90 ngày trước.",
        "average_7": "Trung bình 7 ngày trước: **{value:,.2f} VND/AUD**",
        "average_30": "Trung bình 30 ngày trước: **{value:,.2f} VND/AUD**",
        "history": "Lịch sử tỷ giá",
        "chart_rate": "VND trên mỗi AUD",
        "calculator": "Công cụ quy đổi VND sang AUD",
        "vnd_amount": "Số tiền VND",
        "amount_received": "Số tiền ước tính nhận được: **A${value:,.2f}**",
        "planner": "Lập kế hoạch ngân sách chuyển tiền",
        "aud_amount": "Số AUD cần chuyển",
        "deadline": "Số ngày còn lại đến hạn chuyển tiền",
        "set_budget": "Đặt ngân sách VND tối đa",
        "maximum_budget": "Ngân sách VND tối đa",
        "current_cost": "Chi phí hiện tại cho {amount:,.2f} AUD: **{cost:,.0f} VND**",
        "cost_less": "Hôm nay rẻ hơn khoảng {value:,.0f} VND so với mức trung bình 30 ngày trước.",
        "cost_more": "Hôm nay đắt hơn khoảng {value:,.0f} VND so với mức trung bình 30 ngày trước.",
        "maximum_rate": "Tỷ giá tối đa có thể chi trả: **{value:,.2f} VND/AUD**",
        "within_budget": "Thấp hơn ngân sách {value:,.0f} VND.",
        "over_budget": "Vượt ngân sách {value:,.0f} VND.",
        "no_budget": "Chưa đặt ngân sách tối đa.",
        "close_deadline": "Thời hạn chuyển tiền đã gần. Kết quả kiểm tra lịch sử không cho thấy chờ đợi mang lại lợi thế đáng tin cậy.",
        "no_edge": "Chưa tìm thấy lợi thế đáng tin cậy về thời điểm chuyển tiền. Bảng điều khiển này cung cấp bối cảnh lịch sử và phép tính ngân sách, không phải dự báo được bảo đảm.",
        "model_results": "Kết quả đánh giá mô hình",
        "naive_result": "Sai số MAE của dự báo một ngày đơn giản: **47.59 VND trên mỗi AUD**.",
        "regression_result": "MAE hồi quy cuốn chiếu là **56.51 VND**, so với **53.06 VND** của mô hình cơ sở. Vì vậy mô hình hồi quy đã bị loại.",
        "strategy_result": "Trong kiểm tra lịch sử, chiến lược chọn thời điểm trong 14 ngày tệ hơn trung bình **5.79 VND trên mỗi AUD** so với chuyển ngay, nên chiến lược này đã bị loại.",
    },
}

t = translations[language]


data_file = (
    Path(__file__).parent
    / "data"
    / "vcb_aud_daily.csv"
)

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

dates = [row["date"] for row in rows]
rates = [float(row["sell"]) for row in rows]

latest = rates[-1]
previous = rates[-2]

previous_30_rates = rates[-31:-1]
average_7 = mean(previous_30_rates[-7:])
average_30 = mean(previous_30_rates)

st.title(t["title"])

st.metric(
    t["rate_label"],
    f"{latest:,.2f} VND",
    delta=f"{latest - previous:+,.2f} {t['vs_yesterday']}",
    delta_color="inverse",
)

st.caption(f"{t['last_updated']}: {dates[-1]}")
st.caption(t["lower_is_better"])

st.subheader(t["how_good"])

historical_rates = rates[:-1]
better_than = sum(
    rate > latest
    for rate in historical_rates
)

percentile = (
    better_than
    / len(historical_rates)
    * 100
)

st.write(t["earlier_days"].format(value=percentile))

recent_rates = rates[-91:-1]
better_recent = sum(
    rate > latest
    for rate in recent_rates
)

recent_percentile = (
    better_recent
    / len(recent_rates)
    * 100
)

st.write(t["recent_days"].format(value=recent_percentile))
st.write(t["average_7"].format(value=average_7))
st.write(t["average_30"].format(value=average_30))

st.subheader(t["history"])

chart_rate_label = t["chart_rate"]

chart_data = {
    "date": dates,
    chart_rate_label: rates,
}

st.line_chart(
    chart_data,
    x="date",
    y=chart_rate_label,
)

st.subheader(t["calculator"])

vnd_amount = st.number_input(
    t["vnd_amount"],
    min_value=1_000_000,
    value=56_000_000,
    step=1_000_000,
)

st.write(t["amount_received"].format(value=vnd_amount / latest))

st.divider()
st.subheader(t["planner"])

aud_amount = st.number_input(
    t["aud_amount"],
    min_value=1.0,
    value=3000.0,
    step=100.0,
)

days_remaining = st.number_input(
    t["deadline"],
    min_value=0,
    value=14,
    step=1,
)

use_budget = st.checkbox(t["set_budget"])

maximum_budget_vnd = None

if use_budget:
    maximum_budget_vnd = st.number_input(
        t["maximum_budget"],
        min_value=1_000_000,
        value=57_000_000,
        step=100_000,
    )

current_cost = aud_amount * latest
average_30_cost = aud_amount * average_30
average_cost_difference = (
    average_30_cost - current_cost
)

st.write(
    t["current_cost"].format(
        amount=aud_amount,
        cost=current_cost,
    )
)

if average_cost_difference >= 0:
    st.success(
        t["cost_less"].format(
            value=average_cost_difference
        )
    )
else:
    st.warning(
        t["cost_more"].format(
            value=abs(average_cost_difference)
        )
    )

if maximum_budget_vnd is not None:
    maximum_affordable_rate = (
        maximum_budget_vnd / aud_amount
    )

    budget_difference = (
        maximum_budget_vnd - current_cost
    )

    st.write(
        t["maximum_rate"].format(
            value=maximum_affordable_rate
        )
    )

    if budget_difference >= 0:
        st.success(
            t["within_budget"].format(
                value=budget_difference
            )
        )
    else:
        st.error(
            t["over_budget"].format(
                value=abs(budget_difference)
            )
        )

else:
    st.info(t["no_budget"])

if days_remaining <= 2:
    st.warning(t["close_deadline"])

st.info(t["no_edge"])

with st.expander(t["model_results"]):
    st.write(t["naive_result"])
    st.write(t["regression_result"])
    st.write(t["strategy_result"])

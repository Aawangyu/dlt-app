import streamlit as st
import pandas as pd
import engine

st.set_page_config(page_title="大乐透概率模拟台", layout="wide")
st.title("🎱 大乐透概率模拟与复盘台")
st.caption("百分比是本工具规则里的权重占比，不是真实中奖概率。仅供数据分析与模拟。")

engine.init_db()

# 第一次使用：先下载历史数据
if engine.draw_count() == 0:
    st.warning("第一次使用：请先点下面的按钮下载历史开奖数据，大约等 10 秒。")
    if st.button("① 下载历史开奖数据", type="primary"):
        with st.spinner("正在下载，请稍等..."):
            n = engine.fetch_history()
        st.success(f"下载完成，新增 {n} 条。")
        st.rerun()
    st.stop()

weights = engine.compute_weights()

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 概率总览", "🎲 生成一注", "📋 模拟记录", "🔄 复盘反推"]
)

with tab1:
    st.subheader("前区号码权重占比（%）")
    st.caption("真实开奖里每个号码单期概率固定约 14.29%。这里显示的是本工具规则下的权重。")

    fp_df = pd.DataFrame({
        "号码": list(weights["front_prob"].keys()),
        "权重%": list(weights["front_prob"].values()),
        "当前遗漏": [weights["front_omit"][n] for n in weights["front_prob"]],
        "历史出现次数": [weights["front_freq"][n] for n in weights["front_prob"]],
    }).sort_values("权重%", ascending=False)

    st.bar_chart(fp_df.set_index("号码")["权重%"])
    st.dataframe(fp_df, use_container_width=True, hide_index=True)

    st.subheader("后区号码权重占比（%）")
    bp_df = pd.DataFrame({
        "号码": list(weights["back_prob"].keys()),
        "权重%": list(weights["back_prob"].values()),
        "当前遗漏": [weights["back_omit"][n] for n in weights["back_prob"]],
    }).sort_values("权重%", ascending=False)

    st.dataframe(bp_df, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("按权重和结构约束生成一注")
    st.caption("规则：加权抽样 + 和值 75–110 + 奇偶比 2:3 或 3:2 + 三区不过度集中。")

    target = st.text_input(
        "目标期号（可以不填）",
        placeholder="例如 26130"
    )

    if st.button("🎲 生成并保存一注", type="primary"):
        front, back = engine.generate_one(weights)
        engine.save_prediction(weights, target, front, back)

        st.success(f"前区：{front}  |  后区：{back}")
        st.write("这注号码的权重%：")
        st.write("前区", {n: weights["front_prob"][n] for n in front})
        st.write("后区", {n: weights["back_prob"][n] for n in back})
        st.caption("这条记录已经保存。以后开奖了，去“复盘反推”点一下。")

with tab3:
    st.subheader("所有模拟记录")

    rows = engine.get_predictions()
    if not rows:
        st.info("还没有记录。先去“生成一注”点一次按钮。")
    else:
        df = pd.DataFrame(rows, columns=[
            "ID", "目标期号", "前区", "后区",
            "生成时间", "复盘结果", "前区命中", "后区命中"
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)

        completed = df[df["复盘结果"] != "待开奖"]
        if len(completed) > 0:
            st.subheader("长期汇总")
            c1, c2, c3 = st.columns(3)
            c1.metric("已复盘注数", len(completed))
            c2.metric("前区平均命中", round(completed["前区命中"].mean(), 2))
            c3.metric("后区平均命中", round(completed["后区命中"].mean(), 2))

with tab4:
    st.subheader("开奖后自动复盘")
    st.caption("程序会拿已开奖数据，去匹配所有“待开奖”的记录。")

    if st.button("🔄 执行复盘"):
        engine.review_all()
        st.success("复盘完成，去“模拟记录”看结果。")
        st.rerun()

    st.divider()
    st.markdown("""
    **这里的“反推”实际含义：**

    - 程序不会真的算出下期号码。
    - 它会把你之前生成的号码和实际开奖比对，记录命中几个。
    - 新一期开奖数据加入后，下一次的权重会自动变化。
    - 你通过“模拟记录”长期观察这套规则，而不是指望某一次算中。
    """)
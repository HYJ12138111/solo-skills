---
name: start-my-day
description: 论文阅读工作流启动 - 从Semantic Scholar/PubMed搜索体育科学论文，追加到当日日记
---

# 体育科学论文推荐 — 每日启动

## 目标
搜索体育教学、非线性教学法、运动技能学习等领域最新论文，追加到当日 Obsidian 日记。

用户研究方向：体育人文社会学 → 体育教学 → 非线性教学法（NLP/CLA/生态动力学）。

## 工作流程

### 步骤1：收集上下文
1. 获取今日日期（YYYY-MM-DD 格式）
2. 扫描 `知识库/专题笔记/` 了解研究领域
3. 扫描 `知识库/单篇笔记/` 了解已有论文覆盖

### 步骤2：搜索论文
用 WebSearch 按研究领域关键词搜索近期论文（聚焦体育教学方向）：
- `"nonlinear pedagogy" OR "constraints-led approach" physical education sport 2026`
- `"ecological dynamics" physical education sport coaching 2026`
- `"skill acquisition" OR "motor learning" physical education 2026`
- `"teaching games for understanding" OR "game sense" physical education 2026`
- `"relative age effect" sport talent selection youth 2025 2026`
- 酌情搜索：体育教师教育、体育课程改革、运动员长期发展、创造力与体育教学

### 步骤3：筛选评分

| 维度 | 权重 | 标准 |
|------|------|------|
| 相关性 | 50% | 标题/摘要与研究兴趣的匹配程度 |
| 新近性 | 20% | 3个月内+3分, 半年内+2分, 一年内+1分 |
| 质量 | 30% | 高水平期刊(BJSM/MSSE/JSS/JTPE等)，有实证数据 |

### 步骤4：追加到当日日记
追加到 `日记/YYYY-MM-DD.md` 的「📖 读到的」区块下：

```markdown
### 🔬 今日论文推荐（共N篇）

**趋势**：{一句话}

| # | 论文 | 期刊 | 评分 | 推荐理由 |
|---|------|------|------|----------|
| 1 | [标题](DOI) — 作者 | 期刊 | 4.7 | 理由 |
```

### 步骤5：标注深度分析建议
对前3篇论文提示可执行 `/paper-analyze`。

## 重要规则
- 优先 WebSearch，灵活调整搜索策略
- 某领域无新论文则标注「今日无更新」
- 追加到日记，不创建独立文件
- 不强行推荐不相关论文

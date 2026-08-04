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

### 步骤2：搜索论文（二选一）

**方案A — PubMed 脚本（推荐，结构化评分）**
```bash
python3 scripts/search_pubmed.py \
  --email "你的邮箱@example.com" \
  --target-date YYYY-MM-DD \
  --top-n 10 \
  --output /tmp/pubmed_results.json
```
输出 JSON：含标题/摘要/作者/期刊/DOI + 四维评分（相关性/新近性/期刊质量/研究类型）。
可加 `--focus "nonlinear pedagogy,CLA"` 聚焦特定关键词。

**方案B — WebSearch（备选，覆盖面更广）**
- `"nonlinear pedagogy" OR "constraints-led approach" physical education sport 2026`
- `"ecological dynamics" physical education sport coaching 2026`
- `"skill acquisition" OR "motor learning" physical education 2026`
- `"teaching games for understanding" OR "game sense" physical education 2026`
- `"relative age effect" sport talent selection youth 2025 2026`
- 酌情搜索：体育教师教育、体育课程改革、运动员长期发展、创造力与体育教学

### 步骤3：筛选评分

| 维度 | 权重 | 标准 |
|------|------|------|
| 相关性 | 40% | 标题/摘要中体育教学核心关键词匹配 |
| 期刊质量 | 25% | BJSM/MSSE(JCR Q1)权重高，英文普刊(JCR Q4)权重低 |
| 新近性 | 20% | 3个月内+3分, 半年内+2.5分, 一年内+1.5分 |
| 研究类型 | 15% | 实证研究(RCT/准实验/质性) > 系统综述 > 叙述综述 |

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

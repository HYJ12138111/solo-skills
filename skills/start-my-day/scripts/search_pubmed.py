#!/usr/bin/env python3
"""
PubMed 体育科学论文搜索脚本
替代 search_arxiv.py，通过 NCBI Entrez API 搜索体育教学/运动科学论文。
免费、无需 API Key、无需第三方依赖（仅用标准库 urllib）。
速率限制：3 req/sec（无 API Key），10 req/sec（有 API Key）。

用法:
  python3 search_pubmed.py --output results.json --top-n 10
  python3 search_pubmed.py --target-date 2026-07-05 --focus "nonlinear pedagogy,CLA"
"""

import json
import re
import sys
import time
import ssl
import logging
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)
_SSL_CONTEXT = ssl.create_default_context()
_SSL_CONTEXT.check_hostname = False
_SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# ============================================================
# 配置
# ============================================================

ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
ENTREZ_EMAIL = "user@example.com"  # NCBI 要求提供邮箱
ENTREZ_API_KEY = None  # 可选的 API Key，提升速率至 10 req/sec
RATE_LIMIT_WAIT = 0.35   # 无 API Key 时两次请求间隔（秒），< 3 req/sec

# 研究领域搜索关键词组（OR 连接）
SEARCH_QUERIES = [
    # NLP/CLA/生态动力学（核心）
    '"nonlinear pedagogy" OR "constraints-led approach" OR ("ecological dynamics" AND (sport OR "physical education"))',
    # TGfU/理解式教学
    '"teaching games for understanding" OR "game sense"',
    # 体育教学法
    '("physical education" OR "sport pedagogy") AND ("teaching model" OR "pedagogical model" OR "instructional model")',
    # NLP/CLA 在体育教学中的应用
    '("nonlinear pedagogy" OR "constraints-led") AND ("physical education" OR "school" OR "teaching")',
    # 体育教学法+技能习得
    '("physical education" OR "sport pedagogy") AND ("skill acquisition" OR "motor learning")',
    # SE/TGfU混合模型
    '("sport education" OR "cooperative learning") AND "physical education" AND ("teaching games" OR TGfU OR "hybrid")',
]

# 排除词（过滤不相关论文）
EXCLUDED_TERMS = [
    "rat", "mice", "mouse", "rodent",
    "molecular", "gene", "protein", "cell",
    "surgery", "pharmacolog", "drug",
]

# 期刊质量分级（体育科学）
JOURNAL_TIERS = {
    "tier1": {  # IF > 5
        "British Journal of Sports Medicine",
        "Sports Medicine",
        "Medicine and Science in Sports and Exercise",
        "Journal of Sport and Health Science",
        "American Journal of Sports Medicine",
        "Exercise and Sport Sciences Reviews",
    },
    "tier2": {  # IF 2-5
        "Journal of Sports Sciences",
        "Journal of Teaching in Physical Education",
        "Physical Education and Sport Pedagogy",
        "European Physical Education Review",
        "Journal of Sport & Exercise Psychology",
        "Psychology of Sport and Exercise",
        "Scandinavian Journal of Medicine & Science in Sports",
        "European Journal of Sport Science",
        "International Journal of Sports Physiology and Performance",
        "Research Quarterly for Exercise and Sport",
        "Journal of Science and Medicine in Sport",
        "Journal of Strength and Conditioning Research",
        "Quest",
        "Sport, Education and Society",
        "International Journal of Performance Analysis in Sport",
    },
    "tier3": {  # IF < 2 或地区性期刊
        "Journal of Physical Education and Sport",
        "Curriculum Studies in Health and Physical Education",
        "Sport Sciences for Health",
        "International Journal of Sports Science & Coaching",
    },
}

# 评分常数
SCORE_MAX = 3.0
WEIGHTS = {
    "relevance": 0.40,
    "recency": 0.20,
    "journal_quality": 0.25,
    "study_type": 0.15,
}

# 体育教学核心关键词（标题命中加权）
CORE_KEYWORDS = [
    "nonlinear pedagogy", "non-linear pedagogy", "constraints-led",
    "ecological dynamics", "physical education", "sport pedagogy",
    "teaching games for understanding", "game sense",
    "sport education", "cooperative learning",
    "motor learning", "skill acquisition",
    "movement variability", "functional variability",
    "representative learning", "task simplification",
    "perception-action", "affordance",
    "small-sided games", "creativity",
    "physical literacy", "decision making",
]

# ============================================================
# API 调用
# ============================================================

def _entrez_request(endpoint: str, params: dict) -> str:
    """发送 Entrez API 请求，返回原始响应文本"""
    params.setdefault("email", ENTREZ_EMAIL)
    if ENTREZ_API_KEY:
        params["api_key"] = ENTREZ_API_KEY
    query = urllib.parse.urlencode(params)
    url = f"{ENTREZ_BASE}/{endpoint}.fcgi?{query}"
    with urllib.request.urlopen(url, timeout=30, context=_SSL_CONTEXT) as resp:
        return resp.read().decode("utf-8")
    time.sleep(RATE_LIMIT_WAIT)


def entrez_search(query: str, mindate: str, maxdate: str, retmax: int = 20) -> list[str]:
    """搜索 PubMed，返回 PMID 列表"""
    logger.info("[PubMed] esearch: %s", query[:100])
    xml = _entrez_request("esearch", {
        "db": "pubmed",
        "term": query,
        "retmax": str(retmax),
        "sort": "relevance",
        "mindate": mindate,
        "maxdate": maxdate,
        "datetype": "pdat",
        "retmode": "xml",
    })
    root = ET.fromstring(xml)
    ids = [e.text for e in root.findall(".//Id")]
    logger.info("[PubMed] Found %d PMIDs", len(ids))
    return ids


def entrez_fetch(pmids: list[str]) -> list[dict]:
    """批量获取论文摘要（XML 格式），返回结构化列表"""
    if not pmids:
        return []
    logger.info("[PubMed] efetch: %d PMIDs", len(pmids))
    xml = _entrez_request("efetch", {
        "db": "pubmed",
        "id": ",".join(pmids),
        "rettype": "abstract",
        "retmode": "xml",
    })
    root = ET.fromstring(xml)
    papers = []
    for article in root.findall(".//PubmedArticle"):
        paper = _parse_article(article)
        if paper:
            papers.append(paper)
    return papers


def _parse_article(article: ET.Element) -> Optional[dict]:
    """解析单个 PubmedArticle XML 元素"""
    try:
        # PMID
        pmid_elem = article.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        # 标题
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""
        if not title:
            return None

        # 摘要
        abstract_parts = []
        for ab in article.findall(".//AbstractText"):
            label = ab.get("Label", "")
            text = ab.text or ""
            if text:
                abstract_parts.append(f"{label}: {text}" if label else text)
            # 处理嵌套元素
            for child in ab:
                if child.tail:
                    abstract_parts.append(child.tail)
        abstract = " ".join(abstract_parts)

        # 作者（前5个）
        authors = []
        for auth in article.findall(".//Author")[:5]:
            last = auth.findtext("LastName") or ""
            fore = auth.findtext("ForeName") or ""
            if last:
                authors.append(f"{last} {fore}".strip())
            else:
                collective = auth.findtext("CollectiveName")
                if collective:
                    authors.append(collective)

        # 期刊
        journal_elem = article.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # 日期
        year_elem = article.find(".//PubDate/Year")
        month_elem = article.find(".//PubDate/Month")
        day_elem = article.find(".//PubDate/Day")
        year = year_elem.text if year_elem is not None else ""
        month = month_elem.text if month_elem is not None else "01"
        day = day_elem.text if day_elem is not None else "01"
        try:
            month = f"{int(month):02d}"
            day = f"{int(day):02d}"
        except ValueError:
            month, day = "01", "01"
        pub_date = f"{year}-{month}-{day}" if year else ""

        # DOI
        doi = ""
        for eid in article.findall(".//ArticleIdList/ArticleId"):
            if eid.get("IdType") == "doi":
                doi = eid.text or ""
                break

        # 出版类型
        pub_types = [
            pt.text for pt in article.findall(".//PublicationType")
            if pt.text
        ]

        # MeSH 词条
        mesh_terms = [
            mh.findtext("DescriptorName") for mh in article.findall(".//MeshHeading")
            if mh.findtext("DescriptorName")
        ]

        return {
            "pmid": pmid,
            "title": title.strip(),
            "abstract": abstract.strip(),
            "authors": authors,
            "journal": journal.strip(),
            "pub_date": pub_date,
            "doi": doi,
            "pub_types": pub_types,
            "mesh_terms": mesh_terms,
            "source": "pubmed",
        }
    except Exception as e:
        logger.warning("Error parsing article: %s", e)
        return None


# ============================================================
# 评分逻辑
# ============================================================

def _journal_tier_score(journal: str) -> float:
    """期刊质量评分 (0-3)"""
    j_lower = journal.lower()
    for tier_name, journals in JOURNAL_TIERS.items():
        for j_ref in journals:
            if j_ref.lower() in j_lower:
                return {"tier1": 3.0, "tier2": 2.0, "tier3": 1.0}[tier_name]
    return 0.5


def _relevance_score(title: str, abstract: str, mesh_terms: list[str]) -> tuple[float, list[str]]:
    """相关性评分 (0-3)，基于体育教学核心关键词匹配"""
    text = (title + " " + abstract + " " + " ".join(mesh_terms)).lower()
    score = 0.0
    matched = []
    for kw in CORE_KEYWORDS:
        kw_l = kw.lower()
        if kw_l in title.lower():
            score += 0.6
            matched.append(kw)
        elif kw_l in abstract.lower():
            score += 0.3
            matched.append(kw)
        elif kw_l in " ".join(mesh_terms).lower():
            score += 0.2
            matched.append(kw)
    return min(score, SCORE_MAX), matched


def _recency_score(pub_date_str: str) -> float:
    """新近性评分 (0-3)"""
    if not pub_date_str:
        return 1.0
    try:
        pub = datetime.strptime(pub_date_str[:10], "%Y-%m-%d")
        days = (datetime.now() - pub).days
        if days <= 90:
            return 3.0
        elif days <= 180:
            return 2.5
        elif days <= 365:
            return 1.5
        else:
            return 0.5
    except ValueError:
        return 1.0


def _study_type_score(abstract: str, pub_types: list[str]) -> float:
    """研究类型评分 (0-3)：实证 > 系统综述 > 叙述综述"""
    ab_lower = abstract.lower()
    pt_lower = " ".join(pub_types).lower()

    # 排除纯动物实验
    for term in EXCLUDED_TERMS:
        if term in ab_lower:
            return 0.0

    score = 0.0
    # 实证研究标志
    empirical_signals = [
        "participants", "subjects", "sample", "n =", "n=",
        "randomized", "controlled trial", "intervention",
        "pre-test", "post-test", "experimental group",
        "control group", "quasi-experimental",
    ]
    for s in empirical_signals:
        if s in ab_lower:
            score += 0.5
            break  # 只计一次

    # 方法学描述
    method_signals = [
        "mixed methods", "qualitative", "quantitative",
        "semi-structured interview", "focus group",
        "thematic analysis", "statistical analysis",
        "anova", "regression", "effect size",
    ]
    score += sum(0.3 for s in method_signals if s in ab_lower)

    # 综述检测
    if "systematic review" in ab_lower or "meta-analysis" in ab_lower:
        score += 1.5
    elif "review" in pt_lower or "review" in ab_lower[:200]:
        score += 0.5

    return min(score, SCORE_MAX)


def score_papers(papers: list[dict]) -> list[dict]:
    """筛选 (排除不相关) + 多维评分"""
    scored = []
    for p in papers:
        # 排除词检查
        text = (p["title"] + " " + p["abstract"]).lower()
        if any(term in text for term in EXCLUDED_TERMS):
            continue

        rel, matched = _relevance_score(p["title"], p["abstract"], p.get("mesh_terms", []))
        if rel < 0.5:  # 完全不相关，跳过
            continue

        rec = _recency_score(p.get("pub_date", ""))
        jq = _journal_tier_score(p.get("journal", ""))
        st = _study_type_score(p.get("abstract", ""), p.get("pub_types", []))

        norm = lambda v: (v / SCORE_MAX) * 10  # 归一化到 0-10
        recommendation = (
            norm(rel) * WEIGHTS["relevance"] +
            norm(rec) * WEIGHTS["recency"] +
            norm(jq) * WEIGHTS["journal_quality"] +
            norm(st) * WEIGHTS["study_type"]
        )

        p["scores"] = {
            "relevance": round(rel, 2),
            "recency": round(rec, 2),
            "journal_quality": round(jq, 2),
            "study_type": round(st, 2),
            "recommendation": round(recommendation, 2),
        }
        p["matched_keywords"] = matched
        scored.append(p)

    scored.sort(key=lambda x: x["scores"]["recommendation"], reverse=True)
    return scored


# ============================================================
# 主流程
# ============================================================

def search_all(
    target_date: Optional[str] = None,
    top_n: int = 10,
    focus: Optional[str] = None,
) -> list[dict]:
    """执行全部搜索查询，合并去重，评分排序"""
    if target_date:
        end_date = target_date
    else:
        end_date = datetime.now().strftime("%Y-%m-%d")

    # 回溯一年
    try:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (end_dt - timedelta(days=365)).strftime("%Y-%m-%d")
    except ValueError:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    # 日期格式转换为 PubMed 要求的 YYYY/MM/DD
    mindate = start_date.replace("-", "/")
    maxdate = end_date.replace("-", "/")

    all_pmids = set()
    queries = [f"({focus})"] if focus else SEARCH_QUERIES

    for query in queries:
        try:
            pmids = entrez_search(query, mindate, maxdate, retmax=25)
            all_pmids.update(pmids)
        except Exception as e:
            logger.warning("Search failed for query '%s': %s", query[:60], e)
            continue

    if not all_pmids:
        logger.warning("No papers found")
        return []

    # 批量获取摘要
    pmid_list = list(all_pmids)
    papers = []
    batch_size = 50
    for i in range(0, len(pmid_list), batch_size):
        batch = pmid_list[i:i + batch_size]
        try:
            batch_papers = entrez_fetch(batch)
            papers.extend(batch_papers)
        except Exception as e:
            logger.warning("Fetch batch %d failed: %s", i // batch_size, e)

    # 评分
    scored = score_papers(papers)
    return scored[:top_n]


def main():
    global ENTREZ_EMAIL, ENTREZ_API_KEY
    parser = argparse.ArgumentParser(
        description="PubMed 体育科学论文搜索"
    )
    parser.add_argument("--output", default="pubmed_results.json",
                        help="输出 JSON 文件路径")
    parser.add_argument("--top-n", type=int, default=10,
                        help="返回论文数")
    parser.add_argument("--target-date", default=None,
                        help="目标日期 (YYYY-MM-DD)")
    parser.add_argument("--focus", default=None,
                        help="聚焦关键词，逗号分隔")
    parser.add_argument("--email", default=ENTREZ_EMAIL,
                        help="NCBI Entrez 邮箱（必填）")
    parser.add_argument("--api-key", default=None,
                        help="NCBI API Key（可选，提升速率）")

    args = parser.parse_args()

    ENTREZ_EMAIL = args.email
    ENTREZ_API_KEY = args.api_key or ENTREZ_API_KEY

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    target = args.target_date or datetime.now().strftime("%Y-%m-%d")
    logger.info("=== PubMed 体育科学论文搜索 ===")
    logger.info("Target date: %s, Top N: %d", target, args.top_n)

    top = search_all(
        target_date=target,
        top_n=args.top_n,
        focus=args.focus,
    )

    result = {
        "target_date": target,
        "total": len(top),
        "top_papers": top,
    }

    json_str = json.dumps(result, ensure_ascii=False, indent=2, default=str)
    if args.output in ("-", "/dev/stdout"):
        sys.stdout.write(json_str + "\n")
    else:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_str)
        logger.info("Saved %d papers → %s", len(top), args.output)
        print(json_str)

    # 摘要
    for i, p in enumerate(top, 1):
        s = p["scores"]
        logger.info(
            "  %2d. [%.1f] %s (%s)",
            i, s["recommendation"],
            p["title"][:80], p.get("journal", "")[:30]
        )


if __name__ == "__main__":
    main()

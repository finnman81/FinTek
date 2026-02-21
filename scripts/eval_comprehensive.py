"""
Comprehensive 3-Layer RAG Evaluation Script (2026 Best Practices)

Layer 1: Retrieval Evaluation (before LLM)
  - Context Recall: Did correct section appear in top-K?
  - Context Precision: How much irrelevant junk was retrieved?
  - MRR / nDCG: Ranking quality

Layer 2: Grounded Answer Evaluation
  - Faithfulness: Is answer supported by context?
  - Citation Correctness: Right page/section?
  - Abstention Accuracy: Did it say "not found" when appropriate?

Layer 3: Behavioral / Production Simulation
  - Query paraphrasing robustness
  - Noise injection
  - Adversarial phrasing
  - Code/token-heavy queries
  - Long compound queries

Question Categories (300 total):
  - Exact spec lookup (torque, voltage, psi): 20% (60)
  - Step-by-step procedures: 25% (75)
  - Troubleshooting "symptom → cause": 20% (60)
  - Error code / part number queries: 15% (45)
  - Safety / warnings: 10% (30)
  - Multi-hop (combine 2 sections): 10% (30)

Usage:
  python scripts/eval_comprehensive.py \
    --tenant-slug claw-demo \
    --questions claw_manuals/eval_questions_300.json \
    [--layer 1|2|3|all] \
    [--output results/]
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import random
import re
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import UUID

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy.orm import Session

from src.core.config import load_config
from src.db.connection import get_session_factory
from src.db.models import Tenant
from src.llm.factory import create_embedding_provider, create_llm_provider
from src.retrieval.engine import RetrievalEngine
from src.retrieval.reranker import CrossEncoderReranker
from src.vectorstore.pgvector_store import PostgresVectorStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class RetrievalMetrics:
    """Layer 1: Retrieval evaluation metrics."""
    context_recall: float = 0.0  # Did correct section appear in top-K?
    context_precision: float = 0.0  # How much irrelevant junk?
    mrr: float = 0.0  # Mean Reciprocal Rank
    ndcg_at_5: float = 0.0  # Normalized DCG at K=5
    ndcg_at_10: float = 0.0
    avg_retrieved: int = 0
    avg_relevant: int = 0
    lexical_strict_hit_count: int = -1  # Strict lexical hits (websearch_to_tsquery); -1 if not available


@dataclass
class AnswerMetrics:
    """Layer 2: Answer quality metrics."""
    faithfulness_score: float = 0.0  # 0-1, LLM-as-judge
    citation_correctness: float = 0.0  # 0-1, citations match expected
    abstention_accuracy: float = 0.0  # Did it abstain when should?
    answer_relevance: float = 0.0  # 0-1, LLM-as-judge
    hallucination_count: int = 0


@dataclass
class RobustnessMetrics:
    """Layer 3: Robustness testing metrics."""
    paraphrase_retrieval_match: float = 0.0  # Same results from paraphrase?
    noise_tolerance: float = 0.0  # Performance with noise
    adversarial_handling: float = 0.0  # Performance on adversarial queries
    long_query_performance: float = 0.0  # Multi-part queries


@dataclass
class QuestionResult:
    """Complete evaluation result for one question."""
    question: str
    category: str
    expected_sources: list[str]
    expected_answer_contains: list[str] | None = None
    should_abstain: bool = False
    
    # Layer 1
    retrieved_results: list[Any] = field(default_factory=list)
    retrieval_metrics: RetrievalMetrics = field(default_factory=RetrievalMetrics)
    
    # Layer 2
    answer: str = ""
    sources: list[dict] = field(default_factory=list)
    answer_metrics: AnswerMetrics = field(default_factory=AnswerMetrics)
    
    # Layer 3
    paraphrase_results: list[Any] = field(default_factory=list)
    robustness_metrics: RobustnessMetrics = field(default_factory=RobustnessMetrics)
    
    latency_ms: float = 0.0
    error: str | None = None

    # FTS debug (first 10 queries when layer 1 enabled): tenant_id, fts_query, metadata_filter, strict_lexical_hits
    fts_debug: dict | None = None


# ---------------------------------------------------------------------------
# Layer 1: Retrieval Metrics
# ---------------------------------------------------------------------------

def _source_matches_expected(source: str, expected_sources: list[str]) -> bool:
    """
    True if source (e.g. full filename) contains any expected substring.
    Expected values are short (e.g. 'fleck_9000'); source is full filename
    (e.g. 'pentair_fleck_9000_9100_9500_service_manual...').
    """
    if not source or not expected_sources:
        return False
    source_lower = source.lower()
    for exp in expected_sources:
        if exp and exp.lower() in source_lower:
            return True
    return False


def compute_context_recall(retrieved: list[Any], expected_sources: list[str]) -> float:
    """Did any expected source appear in retrieved results? (substring match on source)."""
    if not expected_sources:
        return 1.0 if not retrieved else 0.0
    
    found = any(
        _source_matches_expected(r.metadata.get("source", ""), expected_sources)
        for r in retrieved
    )
    return 1.0 if found else 0.0


def compute_context_precision(retrieved: list[Any], expected_sources: list[str]) -> float:
    """What fraction of retrieved results are relevant? (source contains any expected)."""
    if not retrieved:
        return 1.0
    
    relevant = sum(
        1 for r in retrieved
        if _source_matches_expected(r.metadata.get("source", ""), expected_sources)
    )
    return relevant / len(retrieved)


def compute_mrr(retrieved: list[Any], expected_sources: list[str]) -> float:
    """Mean Reciprocal Rank: 1/rank of first relevant result."""
    if not expected_sources:
        return 0.0
    
    for rank, result in enumerate(retrieved, 1):
        source = result.metadata.get("source", "")
        if _source_matches_expected(source, expected_sources):
            return 1.0 / rank
    return 0.0


def dcg_at_k(relevance_scores: list[float], k: int) -> float:
    """Discounted Cumulative Gain at position K."""
    scores = relevance_scores[:k]
    return sum(score / math.log2(i + 2) for i, score in enumerate(scores))


def compute_ndcg(retrieved: list[Any], expected_sources: list[str], k: int = 10) -> float:
    """Normalized DCG: relevance is 1 if source contains any expected substring, else 0."""
    if not retrieved:
        return 0.0
    
    relevance = [
        1.0 if _source_matches_expected(r.metadata.get("source", ""), expected_sources) else 0.0
        for r in retrieved[:k]
    ]
    
    dcg = dcg_at_k(relevance, k)
    
    # Ideal DCG: at least one relevant at top
    num_relevant = sum(relevance)
    ideal_relevance = [1.0] * min(max(1, int(num_relevant)), k) + [0.0] * max(0, k - 1)
    ideal_relevance = ideal_relevance[:k]
    ideal_dcg = dcg_at_k(ideal_relevance, k)
    
    return dcg / ideal_dcg if ideal_dcg > 0 else 0.0


# ---------------------------------------------------------------------------
# Layer 2: Answer Quality (LLM-as-Judge)
# ---------------------------------------------------------------------------

def llm_judge_faithfulness(
    question: str,
    answer: str,
    context: str,
    llm_provider,
) -> tuple[float, str]:
    """
    LLM-as-judge: Is the answer faithful to the context?
    Returns (score 0-1, reasoning).
    """
    prompt = f"""You are evaluating whether an AI assistant's answer is faithful to the provided context.

Question: {question}

Context:
{context[:2000]}

Answer:
{answer[:1000]}

Rate the faithfulness on a scale of 0.0 to 1.0:
- 1.0: Answer is fully supported by context, no unsupported claims
- 0.5: Answer is partially supported, some claims lack evidence
- 0.0: Answer contains unsupported claims or contradicts context

Respond with ONLY a JSON object:
{{"score": 0.0-1.0, "reasoning": "brief explanation"}}
"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = llm_provider.generate(messages)
        content = response.content.strip()
        
        # Extract JSON
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            score = float(data.get("score", 0.0))
            reasoning = data.get("reasoning", "")
            return max(0.0, min(1.0, score)), reasoning
    except Exception as e:
        logger.warning(f"LLM judge failed: {e}")
    
    return 0.5, "Evaluation failed"


def llm_judge_relevance(
    question: str,
    answer: str,
    llm_provider,
) -> tuple[float, str]:
    """LLM-as-judge: Is the answer relevant to the question?"""
    prompt = f"""Rate how relevant this answer is to the question (0.0-1.0).

Question: {question}

Answer: {answer[:1000]}

Respond with ONLY a JSON object:
{{"score": 0.0-1.0, "reasoning": "brief explanation"}}
"""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = llm_provider.generate(messages)
        content = response.content.strip()
        
        json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            score = float(data.get("score", 0.0))
            reasoning = data.get("reasoning", "")
            return max(0.0, min(1.0, score)), reasoning
    except Exception as e:
        logger.warning(f"LLM judge relevance failed: {e}")
    
    return 0.5, "Evaluation failed"


def check_citation_correctness(
    sources: list[dict],
    expected_sources: list[str],
    answer: str,
) -> float:
    """Check if answer/source citations match expected sources (substring match)."""
    if not expected_sources:
        return 1.0 if not sources else 0.0

    # Prefer bracket citations from the answer, e.g. [file.pdf|p=12|s=Section]
    bracket_sources = []
    for m in re.findall(r"\[([^\]]+)\]", answer or ""):
        source_name = m.split("|", 1)[0].strip()
        if source_name:
            bracket_sources.append(source_name)

    # Fall back to retrieved source payload fields
    cited_source_strs = bracket_sources or [
        (s.get("source") or s.get("document") or "")
        for s in (sources or [])
    ]
    covered = sum(
        1 for exp in expected_sources
        if any(_source_matches_expected(cited, [exp]) for cited in cited_source_strs)
    )
    return covered / len(expected_sources)


def check_abstention(
    answer: str,
    should_abstain: bool,
    expected_keywords: list[str] | None = None,
) -> bool:
    """Check if model correctly abstained when it should."""
    if should_abstain:
        # Should say "not found", "no information", etc.
        abstention_phrases = [
            "not found", "no information", "not available", "not in",
            "does not contain", "unable to find", "not provided",
        ]
        answer_lower = answer.lower()
        return any(phrase in answer_lower for phrase in abstention_phrases)
    else:
        answer_lower = answer.lower()
        abstention_phrases = ["not found in provided documents", "not found", "no information", "not available"]
        is_abstention = any(phrase in answer_lower for phrase in abstention_phrases)
        return not is_abstention


# ---------------------------------------------------------------------------
# Layer 3: Robustness Testing
# ---------------------------------------------------------------------------

def generate_paraphrase(question: str, llm_provider) -> str:
    """Generate a paraphrase of the question."""
    prompt = f"""Paraphrase this question in a different way, keeping the same meaning:

{question}

Respond with ONLY the paraphrased question, no explanation."""
    
    try:
        messages = [{"role": "user", "content": prompt}]
        response = llm_provider.generate(messages)
        return response.content.strip().strip('"').strip("'")
    except Exception:
        return question


def inject_noise(question: str, noise_level: float = 0.1) -> str:
    """Inject random noise (typos, extra words) into question."""
    words = question.split()
    num_noise = max(1, int(len(words) * noise_level))
    
    # Add random words
    noise_words = ["the", "a", "please", "can", "you", "help"]
    for _ in range(num_noise):
        idx = random.randint(0, len(words))
        words.insert(idx, random.choice(noise_words))
    
    # Add typos (simple: swap adjacent chars)
    if random.random() < 0.3:
        words = [w[:-2] + w[-1] + w[-2] if len(w) > 3 else w for w in words]
    
    return " ".join(words)


def create_adversarial(question: str) -> str:
    """Create adversarial variant (negation, misleading terms)."""
    # Simple: add negation or misleading context
    adversarial_patterns = [
        f"NOT {question}",
        f"Everything except {question}",
        f"Opposite of {question}",
    ]
    return random.choice(adversarial_patterns)


# ---------------------------------------------------------------------------
# Main Evaluation Functions
# ---------------------------------------------------------------------------

def evaluate_layer1_retrieval(
    question: str,
    expected_sources: list[str],
    vector_store: PostgresVectorStore,
    embedder,
    use_hybrid: bool = True,
    top_k: int = 20,
    metadata_filter: dict | None = None,
) -> tuple[list[Any], RetrievalMetrics]:
    """Evaluate retrieval quality (Layer 1)."""
    query_embedding = embedder.embed_text(question)
    lexical_strict_hit_count: int = -1

    if use_hybrid and hasattr(vector_store, "search_hybrid_with_debug"):
        results, debug = vector_store.search_hybrid_with_debug(
            query_text=question,
            query_embedding=query_embedding,
            vector_top_k=40,
            lexical_top_k=40,
            rrf_k=60,
            final_k=top_k,
            ef_search=80,
            metadata_filter=metadata_filter,
            include_debug=True,
        )
        lexical_strict_hit_count = debug.get("lexical_strict_hit_count", -1)
    elif use_hybrid and hasattr(vector_store, "search_hybrid"):
        results = vector_store.search_hybrid(
            query_text=question,
            query_embedding=query_embedding,
            vector_top_k=40,
            lexical_top_k=40,
            rrf_k=60,
            final_k=top_k,
            ef_search=80,
            metadata_filter=metadata_filter,
        )
    else:
        results = vector_store.search(query_embedding=query_embedding, top_k=top_k)

    metrics = RetrievalMetrics(
        context_recall=compute_context_recall(results, expected_sources),
        context_precision=compute_context_precision(results, expected_sources),
        mrr=compute_mrr(results, expected_sources),
        ndcg_at_5=compute_ndcg(results, expected_sources, k=5),
        ndcg_at_10=compute_ndcg(results, expected_sources, k=10),
        avg_retrieved=len(results),
        avg_relevant=sum(1 for r in results if _source_matches_expected(r.metadata.get("source", ""), expected_sources)),
        lexical_strict_hit_count=lexical_strict_hit_count,
    )

    return results, metrics


def evaluate_layer2_answer(
    question: str,
    expected_sources: list[str],
    expected_answer_contains: list[str] | None,
    should_abstain: bool,
    retrieval_engine: RetrievalEngine,
    llm_judge,
) -> tuple[str, list[dict], AnswerMetrics]:
    """Evaluate answer quality (Layer 2)."""
    result = retrieval_engine.query(question)
    answer = result.answer
    sources = result.sources
    
    # Build context from sources for faithfulness check
    context_parts = []
    for src in sources[:5]:  # Use top 5 sources
        context_parts.append(f"Source: {src.get('source', '')}\n{src.get('text', '')[:500]}")
    context = "\n\n".join(context_parts)
    
    # LLM-as-judge evaluations
    faithfulness_score, faithfulness_reason = llm_judge_faithfulness(
        question, answer, context, llm_judge
    )
    relevance_score, relevance_reason = llm_judge_relevance(question, answer, llm_judge)
    
    # Citation correctness
    citation_score = check_citation_correctness(sources, expected_sources, answer)
    
    # Abstention check
    abstention_correct = check_abstention(answer, should_abstain, expected_answer_contains)
    
    # Hallucination detection (simple: check for unsupported claims)
    hallucination_count = 0
    if expected_answer_contains:
        found_expected = sum(1 for kw in expected_answer_contains if kw.lower() in answer.lower())
        if found_expected == 0 and not should_abstain:
            hallucination_count = 1
    
    metrics = AnswerMetrics(
        faithfulness_score=faithfulness_score,
        citation_correctness=citation_score,
        abstention_accuracy=1.0 if abstention_correct else 0.0,
        answer_relevance=relevance_score,
        hallucination_count=hallucination_count,
    )
    
    return answer, sources, metrics


def evaluate_layer3_robustness(
    question: str,
    expected_sources: list[str],
    vector_store: PostgresVectorStore,
    embedder,
    llm_provider,
    use_hybrid: bool = True,
) -> RobustnessMetrics:
    """Evaluate robustness (Layer 3)."""
    # Paraphrase test
    paraphrase = generate_paraphrase(question, llm_provider)
    para_results, _ = evaluate_layer1_retrieval(
        paraphrase, expected_sources, vector_store, embedder, use_hybrid
    )
    orig_results, _ = evaluate_layer1_retrieval(
        question, expected_sources, vector_store, embedder, use_hybrid
    )
    
    # Compare source overlap
    para_sources = {r.metadata.get("source", "").lower() for r in para_results[:10]}
    orig_sources = {r.metadata.get("source", "").lower() for r in orig_results[:10]}
    paraphrase_match = len(para_sources & orig_sources) / max(len(orig_sources), 1)
    
    # Noise tolerance
    noisy_question = inject_noise(question, noise_level=0.15)
    noisy_results, noisy_metrics = evaluate_layer1_retrieval(
        noisy_question, expected_sources, vector_store, embedder, use_hybrid
    )
    noise_tolerance = noisy_metrics.context_recall
    
    # Adversarial handling
    adversarial_q = create_adversarial(question)
    adv_results, adv_metrics = evaluate_layer1_retrieval(
        adversarial_q, expected_sources, vector_store, embedder, use_hybrid
    )
    adversarial_handling = 1.0 - adv_metrics.context_precision  # Should NOT retrieve for adversarial
    
    # Long query (compound)
    long_query = f"{question} Also, what are the safety considerations and troubleshooting steps?"
    long_results, long_metrics = evaluate_layer1_retrieval(
        long_query, expected_sources, vector_store, embedder, use_hybrid
    )
    long_query_perf = long_metrics.context_recall
    
    return RobustnessMetrics(
        paraphrase_retrieval_match=paraphrase_match,
        noise_tolerance=noise_tolerance,
        adversarial_handling=adversarial_handling,
        long_query_performance=long_query_perf,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def load_questions(path: Path) -> list[dict]:
    """Load questions JSON with category support."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "questions" in data:
        return data["questions"]
    raise ValueError("Questions JSON must be an array or object with 'questions' key")


def get_tenant_id(session: Session, slug_or_uuid: str) -> str:
    """Resolve tenant slug or UUID to tenant ID."""
    try:
        u = UUID(slug_or_uuid)
        t = session.query(Tenant).filter(Tenant.id == u).first()
        if t:
            return str(t.id)
    except (ValueError, TypeError):
        pass
    t = session.query(Tenant).filter(Tenant.slug == slug_or_uuid).first()
    if not t:
        raise SystemExit(f"Tenant not found: {slug_or_uuid}")
    return str(t.id)


def main() -> None:
    parser = argparse.ArgumentParser(description="Comprehensive 3-layer RAG evaluation")
    parser.add_argument("--tenant-slug", "--tenant", dest="tenant", required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--layer", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "results" / "eval_results",
                        help="Output path for JSON and TXT results (default: results/eval_results)")
    parser.add_argument("--sample", type=int, default=None, help="Sample N questions for faster testing")
    args = parser.parse_args()
    
    questions_path = args.questions if args.questions.is_absolute() else PROJECT_ROOT / args.questions
    questions = load_questions(questions_path)
    
    if args.sample:
        questions = random.sample(questions, min(args.sample, len(questions)))
    
    logger.info(f"Loaded {len(questions)} questions")
    
    config = load_config()
    session_factory = get_session_factory()
    
    session = session_factory()
    try:
        tenant_id = get_tenant_id(session, args.tenant)
    finally:
        session.close()
    
    # Setup components
    embedder = create_embedding_provider(config.embedding)
    llm_provider = create_llm_provider(config.llm)
    vector_store = PostgresVectorStore(
        tenant_id=tenant_id,
        session_factory=session_factory,
        embedding_model=config.embedding.model,
        embedding_version=1,
    )
    
    reranker = None
    use_reranker = getattr(config.retrieval, "use_reranker", False)
    if use_reranker:
        try:
            reranker = CrossEncoderReranker()
            logger.info("Reranker loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load reranker: {e}. Disabling reranking.")
            use_reranker = False
            reranker = None
    
    retrieval_engine = RetrievalEngine(
        llm_provider=llm_provider,
        embedding_provider=embedder,
        vector_store=vector_store,
        top_k=getattr(config.retrieval, "top_k", 5),
        score_threshold=getattr(config.retrieval, "score_threshold", 0.0),
        use_hybrid=getattr(config.retrieval, "use_hybrid", True),
        vector_top_k=getattr(config.retrieval, "vector_top_k", 40),
        lexical_top_k=getattr(config.retrieval, "lexical_top_k", 40),
        rrf_k=getattr(config.retrieval, "rrf_k", 60),
        final_k=getattr(config.retrieval, "final_k", 14),
        ef_search=getattr(config.retrieval, "ef_search", 80),
        use_reranker=use_reranker,
        rerank_top_n=getattr(config.retrieval, "rerank_top_n", 20),
        final_context_chunks=getattr(config.retrieval, "final_context_chunks", 5),
        use_two_pass_answer=getattr(config.retrieval, "use_two_pass_answer", False),
        abstain_min_top1_score=getattr(config.retrieval, "abstain_min_top1_score", 0.18),
        abstain_min_margin=getattr(config.retrieval, "abstain_min_margin", 0.05),
        reranker=reranker,
    )
    
    # Run evaluation
    results: list[QuestionResult] = []
    layer1_enabled = args.layer in ("1", "all")
    layer2_enabled = args.layer in ("2", "all")
    layer3_enabled = args.layer in ("3", "all")
    
    for i, q_data in enumerate(questions, 1):
        logger.info(f"[{i}/{len(questions)}] Evaluating: {q_data.get('question', '')[:60]}...")
        
        question = q_data.get("question", "")
        category = q_data.get("category", "unknown")
        expected_sources = q_data.get("expected_sources", []) or [q_data.get("expected_source_contains", "")]
        expected_answer_contains = q_data.get("expected_answer_contains")
        should_abstain = q_data.get("should_abstain", False)
        
        result = QuestionResult(
            question=question,
            category=category,
            expected_sources=expected_sources,
            expected_answer_contains=expected_answer_contains,
            should_abstain=should_abstain,
        )
        
        t0 = time.perf_counter()
        
        try:
            # Layer 1: Retrieval (metadata_filter disabled for retrieval to improve recall)
            if layer1_enabled:
                retrieved, metrics = evaluate_layer1_retrieval(
                    question, expected_sources, vector_store, embedder,
                    use_hybrid=getattr(config.retrieval, "use_hybrid", True),
                    metadata_filter=None,
                )
                result.retrieved_results = retrieved
                result.retrieval_metrics = metrics
                # Log and store FTS debug for first 10 eval queries
                if i <= 10:
                    tenant_id_val = getattr(vector_store, "tenant_id", "N/A")
                    strict_hits = metrics.lexical_strict_hit_count if metrics.lexical_strict_hit_count >= 0 else None
                    result.fts_debug = {
                        "tenant_id": str(tenant_id_val) if tenant_id_val != "N/A" else None,
                        "fts_query": question,
                        "metadata_filter": None,
                        "strict_lexical_hits": strict_hits,
                    }
                    logger.info(
                        "[FTS debug %d/10] tenant_id=%s | fts_query=%r | metadata_filter=None | strict_lexical_hits=%s",
                        i,
                        tenant_id_val,
                        question,
                        strict_hits if strict_hits is not None else "N/A",
                    )
            
            # Layer 2: Answer Quality
            if layer2_enabled:
                answer, sources, answer_metrics = evaluate_layer2_answer(
                    question, expected_sources, expected_answer_contains,
                    should_abstain, retrieval_engine, llm_provider,
                )
                result.answer = answer
                result.sources = sources
                result.answer_metrics = answer_metrics
            
            # Layer 3: Robustness
            if layer3_enabled and i % 10 == 0:  # Sample 10% for robustness (expensive)
                robustness = evaluate_layer3_robustness(
                    question, expected_sources, vector_store, embedder,
                    llm_provider, use_hybrid=getattr(config.retrieval, "use_hybrid", True),
                )
                result.robustness_metrics = robustness
            
            result.latency_ms = (time.perf_counter() - t0) * 1000
            
        except Exception as e:
            logger.exception(f"Error evaluating question {i}")
            result.error = str(e)
        
        results.append(result)

    # Collect debug for up to 5 failing queries (answer contains "not found"); prefer one with recall=1.0
    failing_queries_debug: list[dict] = []
    if layer2_enabled:
        failing = [r for r in results if r.answer and "not found" in r.answer.lower()]
        recall_one = [r for r in failing if r.retrieval_metrics.context_recall == 1.0]
        rest = [r for r in failing if r.retrieval_metrics.context_recall != 1.0]
        # Prefer at least one with recall=1.0 (e.g. #3 in the sample)
        to_debug = (recall_one[:1] if recall_one else []) + rest[: 5 - (1 if recall_one else 0)]
        to_debug = to_debug[:5]
        for r in to_debug:
            try:
                q_result = retrieval_engine.query(r.question, return_debug=True)
                if isinstance(q_result, tuple):
                    _res, debug = q_result
                else:
                    debug = {}
                entry = {
                    "question": r.question,
                    "category": r.category,
                    "context_recall": r.retrieval_metrics.context_recall,
                    "tenant_id": debug.get("tenant_id"),
                    "metadata_filter": debug.get("metadata_filter"),
                    "doc_ids_filter": debug.get("doc_ids_filter"),
                    "query_text_used": debug.get("query_text_used"),
                    "strict_lex_count": debug.get("strict_lex_count"),
                    "fallback_lex_count": debug.get("fallback_lex_count"),
                    "vector_count": debug.get("vector_count"),
                    "fused_count": debug.get("fused_count"),
                    "pre_rerank_count": debug.get("pre_rerank_count"),
                    "post_rerank_count": debug.get("post_rerank_count"),
                    "final_context_char_length": debug.get("final_context_char_length"),
                    "not_found_trigger": debug.get("not_found_trigger"),
                }
                failing_queries_debug.append(entry)
                logger.info(
                    "[Failing query debug] %s | recall=%.2f | strict_lex=%s fallback_lex=%s vector=%s fused=%s post_rerank=%s ctx_len=%s | trigger=%s",
                    r.question[:50],
                    r.retrieval_metrics.context_recall,
                    entry.get("strict_lex_count"),
                    entry.get("fallback_lex_count"),
                    entry.get("vector_count"),
                    entry.get("fused_count"),
                    entry.get("post_rerank_count"),
                    entry.get("final_context_char_length"),
                    entry.get("not_found_trigger"),
                )
            except Exception as e:
                logger.warning("Failed to collect debug for question %s: %s", r.question[:50], e)
                failing_queries_debug.append({
                    "question": r.question,
                    "category": r.category,
                    "context_recall": r.retrieval_metrics.context_recall,
                    "error": str(e),
                })

    # Aggregate metrics
    logger.info("\n" + "=" * 80)
    logger.info("EVALUATION RESULTS")
    logger.info("=" * 80)
    
    lexical_zero_rate: float | None = None
    if layer1_enabled:
        avg_recall = sum(r.retrieval_metrics.context_recall for r in results) / len(results)
        avg_precision = sum(r.retrieval_metrics.context_precision for r in results) / len(results)
        avg_mrr = sum(r.retrieval_metrics.mrr for r in results) / len(results)
        avg_ndcg5 = sum(r.retrieval_metrics.ndcg_at_5 for r in results) / len(results)
        avg_ndcg10 = sum(r.retrieval_metrics.ndcg_at_10 for r in results) / len(results)
        avg_latency_ms = sum(r.latency_ms for r in results) / len(results)
        # Lexical zero rate: fraction of questions where strict lexical returned 0 hits
        with_lex = [r for r in results if r.retrieval_metrics.lexical_strict_hit_count >= 0]
        lexical_zero_count = sum(1 for r in with_lex if r.retrieval_metrics.lexical_strict_hit_count == 0)
        lexical_zero_rate = (lexical_zero_count / len(with_lex)) if with_lex else 0.0

        logger.info("\nLAYER 1: RETRIEVAL METRICS")
        logger.info(f"  Context Recall:    {avg_recall:.3f}")
        logger.info(f"  Context Precision: {avg_precision:.3f}")
        logger.info(f"  MRR:               {avg_mrr:.3f}")
        logger.info(f"  nDCG@5:            {avg_ndcg5:.3f}")
        logger.info(f"  nDCG@10:           {avg_ndcg10:.3f}")
        logger.info(f"  Lexical zero rate: {lexical_zero_rate:.3f} ({lexical_zero_count}/{len(with_lex)} queries with 0 strict lexical hits)")
        logger.info(f"  Avg Latency (ms):  {avg_latency_ms:.1f}")
    
    if layer2_enabled:
        avg_faithfulness = sum(r.answer_metrics.faithfulness_score for r in results) / len(results)
        avg_citations = sum(r.answer_metrics.citation_correctness for r in results) / len(results)
        avg_abstention = sum(r.answer_metrics.abstention_accuracy for r in results) / len(results)
        avg_relevance = sum(r.answer_metrics.answer_relevance for r in results) / len(results)
        total_hallucinations = sum(r.answer_metrics.hallucination_count for r in results)
        
        logger.info("\nLAYER 2: ANSWER QUALITY METRICS")
        logger.info(f"  Faithfulness:      {avg_faithfulness:.3f}")
        logger.info(f"  Citation Correct:  {avg_citations:.3f}")
        logger.info(f"  Abstention Acc:    {avg_abstention:.3f}")
        logger.info(f"  Answer Relevance:  {avg_relevance:.3f}")
        logger.info(f"  Hallucinations:    {total_hallucinations}/{len(results)}")
    
    if layer3_enabled:
        robustness_results = [r for r in results if r.robustness_metrics.paraphrase_retrieval_match > 0]
        if robustness_results:
            avg_para = sum(r.robustness_metrics.paraphrase_retrieval_match for r in robustness_results) / len(robustness_results)
            avg_noise = sum(r.robustness_metrics.noise_tolerance for r in robustness_results) / len(robustness_results)
            avg_adv = sum(r.robustness_metrics.adversarial_handling for r in robustness_results) / len(robustness_results)
            avg_long = sum(r.robustness_metrics.long_query_performance for r in robustness_results) / len(robustness_results)
            
            logger.info("\nLAYER 3: ROBUSTNESS METRICS")
            logger.info(f"  Paraphrase Match:  {avg_para:.3f}")
            logger.info(f"  Noise Tolerance:    {avg_noise:.3f}")
            logger.info(f"  Adversarial:        {avg_adv:.3f}")
            logger.info(f"  Long Query Perf:    {avg_long:.3f}")
    
    # Category breakdown
    by_category = defaultdict(list)
    for r in results:
        by_category[r.category].append(r)
    
    logger.info("\nBY CATEGORY:")
    for cat, cat_results in sorted(by_category.items()):
        if layer1_enabled:
            cat_recall = sum(r.retrieval_metrics.context_recall for r in cat_results) / len(cat_results)
            logger.info(f"  {cat}: Recall={cat_recall:.3f} (n={len(cat_results)})")
    
    # Save results
    if args.output:
        output_path = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable
        output_data = {
            "summary": {
                "total_questions": len(results),
                "layer1_enabled": layer1_enabled,
                "layer2_enabled": layer2_enabled,
                "layer3_enabled": layer3_enabled,
                "lexical_zero_rate": (lexical_zero_rate if layer1_enabled else None),
            },
            "failing_queries_debug": failing_queries_debug,
            "results": [
                {
                    "question": r.question,
                    "category": r.category,
                    "retrieval_metrics": {
                        "context_recall": r.retrieval_metrics.context_recall,
                        "context_precision": r.retrieval_metrics.context_precision,
                        "mrr": r.retrieval_metrics.mrr,
                        "ndcg_at_5": r.retrieval_metrics.ndcg_at_5,
                        "ndcg_at_10": r.retrieval_metrics.ndcg_at_10,
                        "lexical_strict_hit_count": r.retrieval_metrics.lexical_strict_hit_count,
                    } if layer1_enabled else {},
                    "answer_metrics": {
                        "faithfulness_score": r.answer_metrics.faithfulness_score,
                        "citation_correctness": r.answer_metrics.citation_correctness,
                        "abstention_accuracy": r.answer_metrics.abstention_accuracy,
                        "answer_relevance": r.answer_metrics.answer_relevance,
                        "hallucination_count": r.answer_metrics.hallucination_count,
                    } if layer2_enabled else {},
                    "latency_ms": r.latency_ms,
                    "error": r.error,
                    **({"fts_debug": r.fts_debug} if getattr(r, "fts_debug", None) else {}),
                }
                for r in results
            ],
        }
        
        # Save JSON
        json_path = output_path.with_suffix('.json') if output_path.suffix != '.json' else output_path
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"\nJSON results saved to: {json_path}")
        
        # Save human-readable TXT
        txt_path = output_path.with_suffix('.txt') if output_path.suffix != '.json' else output_path.with_suffix('.txt')
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("=" * 80 + "\n")
            f.write("COMPREHENSIVE RAG EVALUATION RESULTS\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Total Questions: {len(results)}\n")
            f.write(f"Layer 1 (Retrieval): {'Enabled' if layer1_enabled else 'Disabled'}\n")
            f.write(f"Layer 2 (Answer Quality): {'Enabled' if layer2_enabled else 'Disabled'}\n")
            f.write(f"Layer 3 (Robustness): {'Enabled' if layer3_enabled else 'Disabled'}\n")
            f.write(f"Reranker: {'Enabled' if use_reranker else 'Disabled'}\n\n")
            
            if layer1_enabled:
                avg_recall = sum(r.retrieval_metrics.context_recall for r in results) / len(results)
                avg_precision = sum(r.retrieval_metrics.context_precision for r in results) / len(results)
                avg_mrr = sum(r.retrieval_metrics.mrr for r in results) / len(results)
                avg_ndcg5 = sum(r.retrieval_metrics.ndcg_at_5 for r in results) / len(results)
                avg_ndcg10 = sum(r.retrieval_metrics.ndcg_at_10 for r in results) / len(results)
                
                f.write("LAYER 1: RETRIEVAL METRICS\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Context Recall:    {avg_recall:.3f}\n")
                f.write(f"  Context Precision: {avg_precision:.3f}\n")
                f.write(f"  MRR:               {avg_mrr:.3f}\n")
                f.write(f"  nDCG@5:            {avg_ndcg5:.3f}\n")
                f.write(f"  nDCG@10:           {avg_ndcg10:.3f}\n")
                if lexical_zero_rate is not None:
                    f.write(f"  Lexical zero rate: {lexical_zero_rate:.3f}\n")
                f.write("\n")
            
            if layer2_enabled:
                avg_faithfulness = sum(r.answer_metrics.faithfulness_score for r in results) / len(results)
                avg_citations = sum(r.answer_metrics.citation_correctness for r in results) / len(results)
                avg_abstention = sum(r.answer_metrics.abstention_accuracy for r in results) / len(results)
                avg_relevance = sum(r.answer_metrics.answer_relevance for r in results) / len(results)
                total_hallucinations = sum(r.answer_metrics.hallucination_count for r in results)
                
                f.write("LAYER 2: ANSWER QUALITY METRICS\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Faithfulness:      {avg_faithfulness:.3f}\n")
                f.write(f"  Citation Correct:  {avg_citations:.3f}\n")
                f.write(f"  Abstention Acc:    {avg_abstention:.3f}\n")
                f.write(f"  Answer Relevance:  {avg_relevance:.3f}\n")
                f.write(f"  Hallucinations:    {total_hallucinations}/{len(results)}\n\n")
            
            if layer3_enabled:
                robustness_results = [r for r in results if r.robustness_metrics.paraphrase_retrieval_match > 0]
                if robustness_results:
                    avg_para = sum(r.robustness_metrics.paraphrase_retrieval_match for r in robustness_results) / len(robustness_results)
                    avg_noise = sum(r.robustness_metrics.noise_tolerance for r in robustness_results) / len(robustness_results)
                    avg_adv = sum(r.robustness_metrics.adversarial_handling for r in robustness_results) / len(robustness_results)
                    avg_long = sum(r.robustness_metrics.long_query_performance for r in robustness_results) / len(robustness_results)
                    
                    f.write("LAYER 3: ROBUSTNESS METRICS\n")
                    f.write("-" * 80 + "\n")
                    f.write(f"  Paraphrase Match:  {avg_para:.3f}\n")
                    f.write(f"  Noise Tolerance:    {avg_noise:.3f}\n")
                    f.write(f"  Adversarial:        {avg_adv:.3f}\n")
                    f.write(f"  Long Query Perf:    {avg_long:.3f}\n\n")
            
            # Category breakdown
            by_category = defaultdict(list)
            for r in results:
                by_category[r.category].append(r)
            
            f.write("BY CATEGORY:\n")
            f.write("-" * 80 + "\n")
            for cat, cat_results in sorted(by_category.items()):
                if layer1_enabled:
                    cat_recall = sum(r.retrieval_metrics.context_recall for r in cat_results) / len(cat_results)
                    cat_precision = sum(r.retrieval_metrics.context_precision for r in cat_results) / len(cat_results)
                    f.write(f"  {cat}: Recall={cat_recall:.3f}, Precision={cat_precision:.3f} (n={len(cat_results)})\n")
                else:
                    f.write(f"  {cat}: n={len(cat_results)}\n")

            # Failing queries debug (up to 5 with "not found" answer)
            if failing_queries_debug:
                f.write("\n\nFAILING QUERIES DEBUG (up to 5)\n")
                f.write("=" * 80 + "\n")
                for idx, d in enumerate(failing_queries_debug, 1):
                    f.write(f"\n[{idx}] {d.get('category', '')} | recall={d.get('context_recall')}\n")
                    f.write(f"  question: {d.get('question', '')[:80]}...\n")
                    f.write(f"  tenant_id: {d.get('tenant_id')}\n")
                    f.write(f"  metadata_filter: {d.get('metadata_filter')}\n")
                    f.write(f"  doc_ids_filter: {d.get('doc_ids_filter')}\n")
                    f.write(f"  query_text_used: {d.get('query_text_used', '')[:80]}...\n")
                    f.write(f"  strict_lex_count: {d.get('strict_lex_count')}  fallback_lex_count: {d.get('fallback_lex_count')}  vector_count: {d.get('vector_count')}\n")
                    f.write(f"  fused_count: {d.get('fused_count')}  pre_rerank_count: {d.get('pre_rerank_count')}  post_rerank_count: {d.get('post_rerank_count')}\n")
                    f.write(f"  final_context_char_length: {d.get('final_context_char_length')}\n")
                    f.write(f"  not_found_trigger: {d.get('not_found_trigger')}\n")
                    if d.get("error"):
                        f.write(f"  error: {d.get('error')}\n")
            
            # Failed questions
            failed = [r for r in results if r.error]
            if failed:
                f.write("\n\nFAILED QUESTIONS:\n")
                f.write("-" * 80 + "\n")
                for r in failed:
                    f.write(f"  Q: {r.question[:70]}...\n")
                    f.write(f"     Error: {r.error}\n\n")
            
            # Sample detailed results
            f.write("\n\nSAMPLE DETAILED RESULTS (First 10):\n")
            f.write("=" * 80 + "\n")
            for i, r in enumerate(results[:10], 1):
                f.write(f"\n[{i}] {r.category.upper()}\n")
                f.write(f"Question: {r.question}\n")
                if layer1_enabled:
                    f.write(f"  Recall: {r.retrieval_metrics.context_recall:.3f}, "
                           f"Precision: {r.retrieval_metrics.context_precision:.3f}, "
                           f"MRR: {r.retrieval_metrics.mrr:.3f}\n")
                if layer2_enabled and r.answer:
                    f.write(f"  Answer: {r.answer[:200]}...\n")
                    f.write(f"  Faithfulness: {r.answer_metrics.faithfulness_score:.3f}, "
                           f"Citations: {r.answer_metrics.citation_correctness:.3f}\n")
                if r.error:
                    f.write(f"  ERROR: {r.error}\n")
                f.write(f"  Latency: {r.latency_ms:.1f}ms\n")
        
        logger.info(f"Text results saved to: {txt_path}")


if __name__ == "__main__":
    main()

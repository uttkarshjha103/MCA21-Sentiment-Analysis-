"""
Keyword Extraction and Topic Analysis Service.
Provides TF-IDF keyword extraction, RAKE phrase extraction, and K-means topic clustering.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import re
import math
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


class Keyword:
    """Represents an extracted keyword with scoring metadata."""

    def __init__(
        self,
        text: str,
        frequency: int,
        tfidf_score: float,
        topic_cluster: Optional[str] = None
    ):
        self.text = text
        self.frequency = frequency
        self.tfidf_score = tfidf_score
        self.topic_cluster = topic_cluster

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "frequency": self.frequency,
            "tfidf_score": round(self.tfidf_score, 4),
            "topic_cluster": self.topic_cluster,
        }


class TopicCluster:
    """Represents a cluster of related keywords/topics."""

    def __init__(self, cluster_id: str, keywords: List[str], centroid_terms: List[str]):
        self.cluster_id = cluster_id
        self.keywords = keywords
        self.centroid_terms = centroid_terms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "keywords": self.keywords,
            "centroid_terms": self.centroid_terms,
        }


class TFIDFResult:
    """Holds TF-IDF computation results."""

    def __init__(self, keywords: List[Keyword], vocabulary_size: int, document_count: int):
        self.keywords = keywords
        self.vocabulary_size = vocabulary_size
        self.document_count = document_count
        self.computed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keywords": [kw.to_dict() for kw in self.keywords],
            "vocabulary_size": self.vocabulary_size,
            "document_count": self.document_count,
            "computed_at": self.computed_at.isoformat(),
        }


class KeywordExtractionResult:
    """Full result from keyword extraction including TF-IDF, RAKE phrases, and clusters."""

    def __init__(
        self,
        tfidf_keywords: List[Keyword],
        rake_phrases: List[Dict[str, Any]],
        topic_clusters: List[TopicCluster],
        document_count: int,
    ):
        self.tfidf_keywords = tfidf_keywords
        self.rake_phrases = rake_phrases
        self.topic_clusters = topic_clusters
        self.document_count = document_count
        self.extracted_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tfidf_keywords": [kw.to_dict() for kw in self.tfidf_keywords],
            "rake_phrases": self.rake_phrases,
            "topic_clusters": [tc.to_dict() for tc in self.topic_clusters],
            "document_count": self.document_count,
            "extracted_at": self.extracted_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Stop words (minimal English set – no external dependency required)
# ---------------------------------------------------------------------------
_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "not", "no", "nor",
    "so", "yet", "both", "either", "neither", "each", "few", "more", "most",
    "other", "some", "such", "than", "too", "very", "just", "as", "if",
    "then", "that", "this", "these", "those", "it", "its", "i", "we", "you",
    "he", "she", "they", "me", "us", "him", "her", "them", "my", "our",
    "your", "his", "their", "what", "which", "who", "whom", "when", "where",
    "why", "how", "all", "any", "about", "above", "after", "before", "between",
    "into", "through", "during", "also", "up", "out", "off", "over", "under",
    "again", "further", "once", "here", "there", "while", "although", "because",
    "since", "until", "unless", "however", "therefore", "thus", "hence",
}


def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, split into tokens, remove stop words."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if len(t) > 2 and t not in _STOP_WORDS]
    return tokens


# ---------------------------------------------------------------------------
# TF-IDF implementation (no scikit-learn dependency)
# ---------------------------------------------------------------------------

def _compute_tfidf(documents: List[str], top_n: int = 30) -> List[Keyword]:
    """
    Compute TF-IDF scores for terms across a corpus of documents.

    Args:
        documents: List of text documents.
        top_n: Number of top keywords to return.

    Returns:
        List of Keyword objects sorted by TF-IDF score descending.
    """
    if not documents:
        return []

    tokenized_docs = [_tokenize(doc) for doc in documents]
    n_docs = len(tokenized_docs)

    # Term frequency per document
    tf_per_doc: List[Dict[str, float]] = []
    for tokens in tokenized_docs:
        total = len(tokens) or 1
        counts: Dict[str, int] = Counter(tokens)
        tf_per_doc.append({term: count / total for term, count in counts.items()})

    # Document frequency (number of docs containing each term)
    df: Dict[str, int] = defaultdict(int)
    for tokens in tokenized_docs:
        for term in set(tokens):
            df[term] += 1

    # IDF with smoothing
    idf: Dict[str, float] = {
        term: math.log((1 + n_docs) / (1 + count)) + 1
        for term, count in df.items()
    }

    # Aggregate TF-IDF across all documents (sum)
    tfidf_scores: Dict[str, float] = defaultdict(float)
    for tf in tf_per_doc:
        for term, tf_val in tf.items():
            tfidf_scores[term] += tf_val * idf.get(term, 1.0)

    # Global frequency
    global_freq: Dict[str, int] = Counter()
    for tokens in tokenized_docs:
        global_freq.update(tokens)

    # Build Keyword objects
    sorted_terms = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    keywords = [
        Keyword(
            text=term,
            frequency=global_freq[term],
            tfidf_score=score,
        )
        for term, score in sorted_terms
    ]
    return keywords


# ---------------------------------------------------------------------------
# RAKE (Rapid Automatic Keyword Extraction) implementation
# ---------------------------------------------------------------------------

def _rake_extract(text: str, top_n: int = 15) -> List[Dict[str, Any]]:
    """
    Simple RAKE algorithm for multi-word phrase extraction.

    Phrases are candidate sequences of words between stop-word boundaries.
    Each phrase is scored by the sum of word scores (degree / frequency).

    Args:
        text: Input text.
        top_n: Maximum number of phrases to return.

    Returns:
        List of dicts with 'phrase' and 'score' keys.
    """
    if not text or not text.strip():
        return []

    # Split text into sentences / phrase candidates using stop words as delimiters
    stop_pattern = r"\b(?:" + "|".join(re.escape(w) for w in _STOP_WORDS) + r")\b"
    sentences = re.sub(r"[^\w\s]", " ", text.lower())
    phrase_candidates = re.split(stop_pattern, sentences)

    phrases: List[List[str]] = []
    for candidate in phrase_candidates:
        words = [w.strip() for w in candidate.split() if w.strip() and len(w.strip()) > 2]
        if words:
            phrases.append(words)

    if not phrases:
        return []

    # Word frequency and degree (co-occurrence within phrases)
    word_freq: Dict[str, int] = Counter()
    word_degree: Dict[str, int] = defaultdict(int)

    for phrase in phrases:
        for word in phrase:
            word_freq[word] += 1
            word_degree[word] += len(phrase) - 1  # degree = co-occurrences

    # Word score = degree / frequency
    word_score: Dict[str, float] = {
        word: (word_degree[word] + word_freq[word]) / word_freq[word]
        for word in word_freq
    }

    # Phrase score = sum of word scores
    phrase_scores: List[Tuple[str, float]] = []
    for phrase in phrases:
        phrase_text = " ".join(phrase)
        score = sum(word_score.get(w, 0) for w in phrase)
        phrase_scores.append((phrase_text, score))

    # Deduplicate and sort
    seen: set = set()
    unique_phrases: List[Tuple[str, float]] = []
    for phrase_text, score in sorted(phrase_scores, key=lambda x: x[1], reverse=True):
        if phrase_text not in seen:
            seen.add(phrase_text)
            unique_phrases.append((phrase_text, score))

    return [
        {"phrase": phrase, "score": round(score, 4)}
        for phrase, score in unique_phrases[:top_n]
    ]


# ---------------------------------------------------------------------------
# K-means topic clustering (pure Python, no scikit-learn dependency)
# ---------------------------------------------------------------------------

def _build_term_vectors(
    keywords: List[Keyword],
) -> Tuple[List[str], Dict[str, List[float]]]:
    """
    Build simple one-hot / frequency vectors for each keyword based on
    character n-gram similarity (a lightweight proxy for semantic similarity).
    """
    terms = [kw.text for kw in keywords]
    # Use character bigrams as features
    all_bigrams: set = set()
    term_bigrams: Dict[str, set] = {}
    for term in terms:
        bgs = {term[i : i + 2] for i in range(len(term) - 1)}
        term_bigrams[term] = bgs
        all_bigrams.update(bgs)

    bigram_list = sorted(all_bigrams)
    vectors: Dict[str, List[float]] = {}
    for term in terms:
        vec = [1.0 if bg in term_bigrams[term] else 0.0 for bg in bigram_list]
        vectors[term] = vec

    return bigram_list, vectors


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _kmeans_cluster(
    keywords: List[Keyword],
    n_clusters: int = 5,
    max_iter: int = 20,
) -> List[TopicCluster]:
    """
    Cluster keywords into topic groups using K-means with cosine similarity.

    Args:
        keywords: List of Keyword objects to cluster.
        n_clusters: Number of clusters.
        max_iter: Maximum iterations.

    Returns:
        List of TopicCluster objects.
    """
    if not keywords:
        return []

    n_clusters = min(n_clusters, len(keywords))
    if n_clusters <= 1:
        cluster = TopicCluster(
            cluster_id="cluster_0",
            keywords=[kw.text for kw in keywords],
            centroid_terms=[kw.text for kw in keywords[:3]],
        )
        return [cluster]

    _, vectors = _build_term_vectors(keywords)
    terms = [kw.text for kw in keywords]
    vecs = [vectors[t] for t in terms]

    # Initialize centroids by picking evenly spaced keywords
    step = max(1, len(terms) // n_clusters)
    centroids = [list(vecs[i * step]) for i in range(n_clusters)]

    assignments = [0] * len(terms)

    for _ in range(max_iter):
        # Assignment step
        new_assignments = []
        for vec in vecs:
            sims = [_cosine_similarity(vec, c) for c in centroids]
            new_assignments.append(sims.index(max(sims)))

        if new_assignments == assignments:
            break
        assignments = new_assignments

        # Update step – recompute centroids
        for k in range(n_clusters):
            cluster_vecs = [vecs[i] for i, a in enumerate(assignments) if a == k]
            if cluster_vecs:
                dim = len(cluster_vecs[0])
                new_centroid = [
                    sum(v[d] for v in cluster_vecs) / len(cluster_vecs)
                    for d in range(dim)
                ]
                centroids[k] = new_centroid

    # Build TopicCluster objects
    clusters: List[TopicCluster] = []
    for k in range(n_clusters):
        cluster_terms = [terms[i] for i, a in enumerate(assignments) if a == k]
        if not cluster_terms:
            continue
        # Top 3 terms by TF-IDF score as centroid labels
        cluster_kws = [kw for kw in keywords if kw.text in cluster_terms]
        cluster_kws.sort(key=lambda kw: kw.tfidf_score, reverse=True)
        centroid_terms = [kw.text for kw in cluster_kws[:3]]
        clusters.append(
            TopicCluster(
                cluster_id=f"cluster_{k}",
                keywords=cluster_terms,
                centroid_terms=centroid_terms,
            )
        )

    return clusters


# ---------------------------------------------------------------------------
# KeywordExtractor – main public class
# ---------------------------------------------------------------------------

class KeywordExtractor:
    """
    Keyword extraction and topic analysis service.

    Combines TF-IDF scoring, RAKE phrase extraction, and K-means topic
    clustering to provide comprehensive keyword analysis.
    """

    def __init__(self, top_n_keywords: int = 30, top_n_phrases: int = 15, n_clusters: int = 5):
        self.top_n_keywords = top_n_keywords
        self.top_n_phrases = top_n_phrases
        self.n_clusters = n_clusters
        logger.info("KeywordExtractor initialised (TF-IDF + RAKE + K-means)")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_keywords(self, texts: List[str]) -> List[Keyword]:
        """
        Extract keywords from a list of texts using TF-IDF.

        Args:
            texts: List of text documents.

        Returns:
            List of Keyword objects sorted by TF-IDF score.
        """
        clean = [t for t in texts if t and t.strip()]
        if not clean:
            return []
        return _compute_tfidf(clean, top_n=self.top_n_keywords)

    def calculate_tfidf_scores(self, texts: List[str]) -> TFIDFResult:
        """
        Compute TF-IDF scores and return a structured result.

        Args:
            texts: List of text documents.

        Returns:
            TFIDFResult with keywords, vocabulary size, and document count.
        """
        clean = [t for t in texts if t and t.strip()]
        keywords = _compute_tfidf(clean, top_n=self.top_n_keywords)
        vocab: set = set()
        for text in clean:
            vocab.update(_tokenize(text))
        return TFIDFResult(
            keywords=keywords,
            vocabulary_size=len(vocab),
            document_count=len(clean),
        )

    def extract_rake_phrases(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Extract multi-word phrases using the RAKE algorithm.

        Args:
            texts: List of text documents.

        Returns:
            List of dicts with 'phrase' and 'score' keys.
        """
        combined = " ".join(t for t in texts if t and t.strip())
        return _rake_extract(combined, top_n=self.top_n_phrases)

    def cluster_topics(self, keywords: List[Keyword]) -> List[TopicCluster]:
        """
        Cluster keywords into topic groups using K-means.

        Args:
            keywords: List of Keyword objects.

        Returns:
            List of TopicCluster objects.
        """
        return _kmeans_cluster(keywords, n_clusters=self.n_clusters)

    def analyze(self, texts: List[str]) -> KeywordExtractionResult:
        """
        Full keyword extraction and topic analysis pipeline.

        Runs TF-IDF extraction, RAKE phrase extraction, and K-means
        clustering in a single call.

        Args:
            texts: List of text documents.

        Returns:
            KeywordExtractionResult with all analysis results.
        """
        clean = [t for t in texts if t and t.strip()]
        logger.info(f"Running keyword analysis on {len(clean)} documents")

        tfidf_keywords = self.extract_keywords(clean)
        rake_phrases = self.extract_rake_phrases(clean)
        topic_clusters = self.cluster_topics(tfidf_keywords)

        # Annotate keywords with their cluster assignment
        term_to_cluster: Dict[str, str] = {}
        for cluster in topic_clusters:
            for term in cluster.keywords:
                term_to_cluster[term] = cluster.cluster_id

        for kw in tfidf_keywords:
            kw.topic_cluster = term_to_cluster.get(kw.text)

        return KeywordExtractionResult(
            tfidf_keywords=tfidf_keywords,
            rake_phrases=rake_phrases,
            topic_clusters=topic_clusters,
            document_count=len(clean),
        )

    def get_info(self) -> Dict[str, Any]:
        """Return configuration info about this extractor."""
        return {
            "top_n_keywords": self.top_n_keywords,
            "top_n_phrases": self.top_n_phrases,
            "n_clusters": self.n_clusters,
            "algorithms": ["TF-IDF", "RAKE", "K-means"],
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_keyword_extractor: Optional[KeywordExtractor] = None


def get_keyword_extractor() -> KeywordExtractor:
    """Return (or create) the global KeywordExtractor instance."""
    global _keyword_extractor
    if _keyword_extractor is None:
        _keyword_extractor = KeywordExtractor()
    return _keyword_extractor

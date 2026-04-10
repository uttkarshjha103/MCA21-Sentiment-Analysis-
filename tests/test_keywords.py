"""
Unit tests for the KeywordExtractor service (task 5.5).
Tests TF-IDF extraction, RAKE phrase extraction, K-means clustering, and the full pipeline.
"""

import pytest
from app.services.keywords import (
    KeywordExtractor,
    Keyword,
    TopicCluster,
    TFIDFResult,
    KeywordExtractionResult,
    _compute_tfidf,
    _rake_extract,
    _kmeans_cluster,
    _tokenize,
    get_keyword_extractor,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_TEXTS = [
    "The government policy on environmental regulation needs urgent reform.",
    "Citizens demand better environmental protection and cleaner air quality.",
    "Economic growth must be balanced with environmental sustainability.",
    "Public consultation on climate change policy is essential for democracy.",
    "Renewable energy investment is critical for reducing carbon emissions.",
    "The new regulation will impact small businesses and economic development.",
    "Community feedback on urban planning and infrastructure is important.",
    "Digital transformation in government services improves citizen experience.",
]


@pytest.fixture
def extractor():
    return KeywordExtractor(top_n_keywords=20, top_n_phrases=10, n_clusters=3)


# ---------------------------------------------------------------------------
# Tokenizer tests
# ---------------------------------------------------------------------------

def test_tokenize_removes_stop_words():
    tokens = _tokenize("the quick brown fox jumps over the lazy dog")
    assert "the" not in tokens
    assert "over" not in tokens
    assert "fox" in tokens
    assert "quick" in tokens


def test_tokenize_lowercases():
    tokens = _tokenize("Environmental POLICY Reform")
    assert "environmental" in tokens
    assert "policy" in tokens
    assert "reform" in tokens


def test_tokenize_removes_short_words():
    tokens = _tokenize("a an it is do be")
    # All are stop words or too short
    assert tokens == []


def test_tokenize_empty_string():
    assert _tokenize("") == []


# ---------------------------------------------------------------------------
# TF-IDF tests
# ---------------------------------------------------------------------------

def test_tfidf_returns_keywords(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    assert len(keywords) > 0
    assert all(isinstance(kw, Keyword) for kw in keywords)


def test_tfidf_scores_are_positive(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    for kw in keywords:
        assert kw.tfidf_score > 0


def test_tfidf_keywords_sorted_by_score(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    scores = [kw.tfidf_score for kw in keywords]
    assert scores == sorted(scores, reverse=True)


def test_tfidf_frequency_is_positive(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    for kw in keywords:
        assert kw.frequency >= 1


def test_tfidf_empty_input(extractor):
    keywords = extractor.extract_keywords([])
    assert keywords == []


def test_tfidf_empty_strings(extractor):
    keywords = extractor.extract_keywords(["", "   ", ""])
    assert keywords == []


def test_calculate_tfidf_scores_returns_result(extractor):
    result = extractor.calculate_tfidf_scores(SAMPLE_TEXTS)
    assert isinstance(result, TFIDFResult)
    assert result.document_count == len(SAMPLE_TEXTS)
    assert result.vocabulary_size > 0
    assert len(result.keywords) > 0


def test_tfidf_result_to_dict(extractor):
    result = extractor.calculate_tfidf_scores(SAMPLE_TEXTS)
    d = result.to_dict()
    assert "keywords" in d
    assert "vocabulary_size" in d
    assert "document_count" in d
    assert "computed_at" in d


def test_keyword_to_dict():
    kw = Keyword(text="policy", frequency=5, tfidf_score=0.75, topic_cluster="cluster_0")
    d = kw.to_dict()
    assert d["text"] == "policy"
    assert d["frequency"] == 5
    assert d["tfidf_score"] == 0.75
    assert d["topic_cluster"] == "cluster_0"


# ---------------------------------------------------------------------------
# RAKE tests
# ---------------------------------------------------------------------------

def test_rake_returns_phrases(extractor):
    phrases = extractor.extract_rake_phrases(SAMPLE_TEXTS)
    assert len(phrases) > 0
    for p in phrases:
        assert "phrase" in p
        assert "score" in p


def test_rake_scores_are_positive(extractor):
    phrases = extractor.extract_rake_phrases(SAMPLE_TEXTS)
    for p in phrases:
        assert p["score"] > 0


def test_rake_phrases_sorted_by_score(extractor):
    phrases = extractor.extract_rake_phrases(SAMPLE_TEXTS)
    scores = [p["score"] for p in phrases]
    assert scores == sorted(scores, reverse=True)


def test_rake_empty_input(extractor):
    phrases = extractor.extract_rake_phrases([])
    assert phrases == []


def test_rake_empty_strings(extractor):
    phrases = extractor.extract_rake_phrases(["", "  "])
    assert phrases == []


def test_rake_single_text():
    phrases = _rake_extract("environmental policy reform is needed for sustainable development")
    assert len(phrases) > 0
    # Multi-word phrases should appear
    phrase_texts = [p["phrase"] for p in phrases]
    assert any(len(p.split()) > 1 for p in phrase_texts)


# ---------------------------------------------------------------------------
# K-means clustering tests
# ---------------------------------------------------------------------------

def test_cluster_topics_returns_clusters(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    clusters = extractor.cluster_topics(keywords)
    assert len(clusters) > 0
    assert all(isinstance(c, TopicCluster) for c in clusters)


def test_cluster_ids_are_unique(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    clusters = extractor.cluster_topics(keywords)
    ids = [c.cluster_id for c in clusters]
    assert len(ids) == len(set(ids))


def test_cluster_keywords_cover_all_terms(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    clusters = extractor.cluster_topics(keywords)
    all_clustered = {term for c in clusters for term in c.keywords}
    all_terms = {kw.text for kw in keywords}
    assert all_terms == all_clustered


def test_cluster_centroid_terms_are_subset(extractor):
    keywords = extractor.extract_keywords(SAMPLE_TEXTS)
    clusters = extractor.cluster_topics(keywords)
    for cluster in clusters:
        for term in cluster.centroid_terms:
            assert term in cluster.keywords


def test_cluster_empty_keywords():
    clusters = _kmeans_cluster([])
    assert clusters == []


def test_cluster_single_keyword():
    kw = Keyword(text="policy", frequency=3, tfidf_score=0.5)
    clusters = _kmeans_cluster([kw], n_clusters=3)
    assert len(clusters) == 1
    assert clusters[0].keywords == ["policy"]


def test_topic_cluster_to_dict():
    cluster = TopicCluster(
        cluster_id="cluster_0",
        keywords=["policy", "reform", "government"],
        centroid_terms=["policy", "reform"],
    )
    d = cluster.to_dict()
    assert d["cluster_id"] == "cluster_0"
    assert "policy" in d["keywords"]
    assert "policy" in d["centroid_terms"]


# ---------------------------------------------------------------------------
# Full pipeline tests
# ---------------------------------------------------------------------------

def test_analyze_returns_full_result(extractor):
    result = extractor.analyze(SAMPLE_TEXTS)
    assert isinstance(result, KeywordExtractionResult)
    assert len(result.tfidf_keywords) > 0
    assert len(result.rake_phrases) > 0
    assert len(result.topic_clusters) > 0
    assert result.document_count == len(SAMPLE_TEXTS)


def test_analyze_keywords_have_cluster_assignment(extractor):
    result = extractor.analyze(SAMPLE_TEXTS)
    # At least some keywords should have a cluster assigned
    assigned = [kw for kw in result.tfidf_keywords if kw.topic_cluster is not None]
    assert len(assigned) > 0


def test_analyze_empty_input(extractor):
    result = extractor.analyze([])
    assert result.document_count == 0
    assert result.tfidf_keywords == []
    assert result.rake_phrases == []


def test_analyze_to_dict(extractor):
    result = extractor.analyze(SAMPLE_TEXTS)
    d = result.to_dict()
    assert "tfidf_keywords" in d
    assert "rake_phrases" in d
    assert "topic_clusters" in d
    assert "document_count" in d
    assert "extracted_at" in d


def test_analyze_filters_empty_strings(extractor):
    texts_with_empty = SAMPLE_TEXTS + ["", "   ", ""]
    result = extractor.analyze(texts_with_empty)
    assert result.document_count == len(SAMPLE_TEXTS)


# ---------------------------------------------------------------------------
# Singleton tests
# ---------------------------------------------------------------------------

def test_get_keyword_extractor_returns_same_instance():
    e1 = get_keyword_extractor()
    e2 = get_keyword_extractor()
    assert e1 is e2


def test_extractor_get_info(extractor):
    info = extractor.get_info()
    assert "top_n_keywords" in info
    assert "top_n_phrases" in info
    assert "n_clusters" in info
    assert "algorithms" in info
    assert "TF-IDF" in info["algorithms"]
    assert "RAKE" in info["algorithms"]
    assert "K-means" in info["algorithms"]

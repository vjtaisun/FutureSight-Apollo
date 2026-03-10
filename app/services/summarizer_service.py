import re
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "to", "for", "of", "in", "on", "at", "it",
    "is", "was", "are", "were", "this", "that", "with", "as", "by", "from", "be", "been",
    "have", "has", "had", "i", "we", "you", "they", "he", "she", "them", "my", "our",
}


def extract_keywords(reviews: list[str], top_n: int = 10) -> list[str]:
    tokens: list[str] = []
    for review in reviews:
        words = re.findall(r"[a-zA-Z]{3,}", review.lower())
        tokens.extend(word for word in words if word not in STOPWORDS)

    counts = Counter(tokens)
    return [word for word, _ in counts.most_common(top_n)]


def build_summary(reviews: list[str], ratings: list[float], keywords: list[str]) -> str:
    total = len(reviews)
    avg_part = ""
    if ratings:
        avg_rating = round(sum(ratings) / len(ratings), 2)
        avg_part = f" Average rating is {avg_rating}/5."

    keyword_part = ""
    if keywords:
        keyword_part = f" Common themes include: {', '.join(keywords[:5])}."

    return f"Analyzed {total} reviews.{avg_part}{keyword_part}".strip()


def ratings_distribution(ratings: list[float]) -> dict[str, int]:
    if not ratings:
        return {}

    rounded = [str(int(round(value))) for value in ratings]
    return dict(Counter(rounded))

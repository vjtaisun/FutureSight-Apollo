CSV_CONTEXT_PROMPT = (
    "Use the following CSV data as external knowledge. "
    "Answer the user's question based only on this data when relevant."
)


def get_csv_context_prompt() -> str:
    return CSV_CONTEXT_PROMPT

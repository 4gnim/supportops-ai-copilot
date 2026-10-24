from supportops.knowledge_base import rebuild_knowledge_index


def main() -> None:
    summary = rebuild_knowledge_index()
    print("Knowledge index rebuilt successfully.")
    print(f"Documents indexed: {summary['documents']}")
    print(f"Chunks indexed:    {summary['chunks']}")


if __name__ == "__main__":
    main()

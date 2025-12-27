from brain.enriched_retriever import get_hybrid_context
from brain.enriched_generator import generate_threat_report

def main():
    print("🛡️ Enriched Cyber Threat Intelligence Reporter (VT + OTX)")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Enter your query: ")
        if query.lower() in ["exit", "quit"]:
            break

        print("\n🔍 Retrieving enriched threat intelligence...")
        context = get_hybrid_context(query)

        print("🧠 Generating SOC intelligence report...\n")
        report = generate_threat_report(query, context)

        print("=" * 60)
        print("FINAL ENRICHED THREAT BRIEF")
        print("=" * 60)
        print(report)
        print("=" * 60 + "\n")

if __name__ == "__main__":
    main()

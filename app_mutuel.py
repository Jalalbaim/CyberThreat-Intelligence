# ==============================
# CONFIGURATION
# ==============================
MULTI_SOURCE = True   # Set to False to disable VT + OTX enrichment
# ==============================

if MULTI_SOURCE:
    from brain_enriched.enriched_retriever import get_hybrid_context
    from brain_enriched.enriched_generator import generate_threat_report
else:
    from brain.retriever import get_hybrid_context
    from brain.generator import generate_threat_report


def main():
    if MULTI_SOURCE:
        print("🛡️ Enriched Cyber Threat Intelligence Reporter (OTX + VT)")
    else:
        print("🛡️ Cyber Threat Intelligence Reporter (OTX only)")

    print("Type 'exit' to quit.\n")

    while True:
        query = input("Enter your query: ")
        if query.lower() in ["exit", "quit"]:
            break

        print("\n🔍 Retrieving threat intelligence...")
        context = get_hybrid_context(query)

        print("🧠 Generating SOC intelligence report...\n")
        report = generate_threat_report(query, context)

        print("=" * 60)
        print("FINAL THREAT BRIEF")
        print("=" * 60)
        print(report)
        print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

from brain.retriever import get_hybrid_context
from brain.generator import generate_threat_report

def main():
    print("Cyber Threat Intelligence Reporter Active")
    user_query = input("\nEnter your query: ")

    print("Searching last 60 minutes of data...")
    context = get_hybrid_context(user_query)
    
    print("Generating intelligence report via Gemma 3:4b...")
    report = generate_threat_report(user_query, context)
    
    print("\n" + "="*100)
    print("FINAL THREAT BRIEF")
    print("="*100)
    print(report)

if __name__ == "__main__":
    main()
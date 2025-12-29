import ollama

def generate_threat_report(query, context):
    system_prompt = (
        "You are an expert Cyber Threat Intelligence Analyst. "
        "Based ONLY on the provided real-time data from the last 60 minutes, "
        # "provide a concise summary, a list of IoCs, and a recommended patch/mitigation priority."
    )
    
    full_prompt = f"{system_prompt}\n\nUSER QUERY: {query}\n\nDATA CONTEXT:\n{context}"
    
    try:
        response = ollama.generate(
            model="gemma3:4b",
            prompt=full_prompt
        )
        return response['response']
    except Exception as e:
        return f"Error generating report: {str(e)}"
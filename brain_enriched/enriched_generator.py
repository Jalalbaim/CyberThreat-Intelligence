import ollama

def generate_threat_report(query, context):
    system_prompt = (
    "You are a senior Cyber Threat Intelligence (CTI) analyst working in a SOC.\n"
    "You MUST base your answer ONLY on the provided threat intelligence context.\n"
    "Do NOT invent dates, timelines, threat actors, or locations.\n"
    "If no explicit date is present in the context, say 'recently observed'.\n"
    "Always quote VirusTotal detection counts numerically when available "
    "(e.g., '41/70 engines detected this hash as malicious').\n"
    "Use concise, professional SOC report language.\n"
    "\n"
    "SOURCE HANDLING RULES:\n"
    "- If the source of a threat is explicitly stated (e.g. CERT-FR, OTX), "
    "you MUST clearly mention it in your answer.\n"
    "- If multiple sources are present, list them.\n"
    "- Do NOT infer or guess sources that are not explicitly written.\n"
    "\n"
    "If no relevant threat data is found, clearly state that no matching "
    "threat intelligence was observed."
)



    user_prompt = f"""
USER QUESTION:
{query}

THREAT INTELLIGENCE CONTEXT:
{context}

TASK:
Provide a concise threat summary suitable for a SOC report.
"""

    try:
        response = ollama.generate(
            model="gemma3:1b",
            prompt=system_prompt + "\n\n" + user_prompt
        )
        return response["response"]
    except Exception as e:
        return f"Error generating report: {str(e)}"

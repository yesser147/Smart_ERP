import sys
import os
import json
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.nl_assistant.nl_query_assistant import HRQueryAssistant

def start_chat():
    assistant = HRQueryAssistant()
    
    print("===============22222===================================================")
    print("🤖 HR NATURAL LANGUAGE INTERACTIVE ASSISTANT")
    print("   Ask any HR/Finance question across your database views.")
    print("   Type 'exit' or 'quit' to stop.")
    print("==================================================================\n")

    while True:
        try:
            user_question = input("👤 You: ").strip()
            
            if not user_question:
                continue
                
            if user_question.lower() in ["exit", "quit", "q"]:
                print("\nEnding session. Goodbye!")
                break
                
            start_time = time.time()
            result = assistant.ask(user_question)
            elapsed = time.time() - start_time
            
            if "error" in result and result.get("error"):
                print(f"\n❌ ERROR ({elapsed:.2f}s): {result['error']}\n")
                continue

            print(f"\n⚡ Response Time: {elapsed:.2f}s")
            print(f"🔍 Executed SQL:\n   {result.get('sql_query')}\n")
            print(f"📝 Executive Summary:\n   {result.get('summary')}\n")
            
            data = result.get("tabular_data", [])
            print(f"📊 Tabular Data ({len(data)} rows):")
            if data:
                print(json.dumps(data[:3], indent=2, default=str))
                if len(data) > 3:
                    print(f"   ... ({len(data) - 3} additional rows truncated)")
            else:
                print("   [No matching records found]")
            print("-" * 66 + "\n")

        except KeyboardInterrupt:
            print("\nSession interrupted. Exiting...")
            break

if __name__ == "__main__":
    start_chat()
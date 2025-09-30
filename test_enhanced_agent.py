#!/usr/bin/env python3
"""
Test script to verify the enhanced CFO Copilot can handle various question types
"""

from agent.planner import plan_and_run

def test_questions():
    """Test various question types"""
    
    test_cases = [
        # Original 4 questions
        "What was June 2025 revenue vs budget in USD?",
        "Show Gross Margin % trend for the last 3 months",
        "Break down Opex by category for June 2025",
        "What is our cash runway right now?",
        
        # New question types
        "What's our latest revenue?",
        "Show me revenue trend for last 6 months",
        "What are our COGS for March 2025?",
        "What's our EBITDA for latest month?",
        "Show me cash balance for June 2025",
        "How is revenue growing?",
        "Give me a financial summary for June 2025",
        "What's our performance this month?",
        "Show me total Opex for May 2025",
        "Compare revenue vs budget",
        "What's our gross margin for latest month?",
        
        # Edge cases
        "How are we doing financially?",
        "Show me key metrics",
        "What's the financial overview?",
        "Tell me about our profitability",
        "How much cash do we have?",
    ]
    
    print("Testing Enhanced CFO Copilot")
    print("=" * 50)
    
    success_count = 0
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{i}. Question: {question}")
        try:
            intent, payload, text = plan_and_run(question)
            print(f"   Intent: {intent}")
            print(f"   Answer: {text[:100]}{'...' if len(text) > 100 else ''}")
            
            if intent != "unknown":
                success_count += 1
                print("   SUCCESS")
            else:
                print("   FAILED (unknown intent)")
                
        except Exception as e:
            print(f"   ERROR: {str(e)}")
    
    print(f"\n" + "=" * 50)
    print(f"Results: {success_count}/{len(test_cases)} questions handled successfully")
    print(f"Success Rate: {(success_count/len(test_cases)*100):.1f}%")
    
    if success_count == len(test_cases):
        print("All questions handled successfully!")
    elif success_count >= len(test_cases) * 0.8:
        print("Most questions handled successfully!")
    else:
        print("Some questions need improvement")

if __name__ == "__main__":
    test_questions()
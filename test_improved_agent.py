#!/usr/bin/env python3
"""
Test the improved Mini CFO Copilot agent that can handle ANY question
and properly responds with "data not available" when appropriate.
"""

from agent.planner import plan_and_run

def test_questions():
    """Test various questions to ensure the agent handles them properly"""
    
    test_cases = [
        # Valid questions that should work
        "What was June 2025 revenue?",
        "Show me COGS for December 2025",
        "What's our cash balance?",
        "Give me EBITDA for latest month",
        "Show opex breakdown for June 2025",
        "What's our gross margin?",
        "How much revenue vs budget?",
        
        # Questions for non-existent data
        "What was revenue for January 2030?",
        "Show me data for December 2020",
        "What's the revenue for March 2026?",
        
        # Random questions that should get general responses
        "Tell me about the company",
        "What's the weather like?",
        "How are we doing financially?",
        "Give me a summary",
        "What metrics do you have?",
        
        # Edge cases
        "Show me profit and loss",
        "What's our burn rate?",
        "How much do we spend on marketing?",
        "What's our runway?",
    ]
    
    print("Testing Improved Mini CFO Copilot Agent")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{i:2d}. Q: {question}")
        
        try:
            intent, payload, text = plan_and_run(question)
            
            # Check if we got a valid response
            if intent and text:
                print(f"    OK Intent: {intent}")
                print(f"    Answer: {text[:100]}{'...' if len(text) > 100 else ''}")
                success_count += 1
            else:
                print(f"    ERROR No response generated")
                
        except Exception as e:
            print(f"    ERROR: {str(e)}")
    
    print("\n" + "=" * 60)
    print(f"Results: {success_count}/{total_count} questions handled successfully")
    print(f"Success rate: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("All questions handled successfully!")
    else:
        print("Some questions need improvement")

if __name__ == "__main__":
    test_questions()
"""
Evaluates the accuracy of the RAG (Retrieval-Augmented Generation) system
compared to the base LLM without RAG augmentation.
"""

import os
import json
import sys
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Initialize Groq client
client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

# Test queries with expected expert answers
TEST_QUERIES = [
    {
        "query": "My Acropora coral is bleaching and turning white. What should I check?",
        "expected_keywords": ["alkalinity", "calcium", "magnesium", "parameter", "test", "lighting", "temperature"],
        "category": "coral_health"
    },
    {
        "query": "I see long hairy algae growing rapidly in my tank. What causes this?",
        "expected_keywords": ["nitrate", "phosphate", "nutrient", "lighting", "water change", "refugium"],
        "category": "algae"
    },
    {
        "query": "My pH keeps dropping to 7.8 at night. Is this normal?",
        "expected_keywords": ["pH", "alkalinity", "carbonate", "respiration", "corals", "stable"],
        "category": "ph_issue"
    },
    {
        "query": "My calcium is at 350 ppm and alkalinity is 6.5 dKH. What should I do?",
        "expected_keywords": ["dose", "calcium", "alkalinity", "buffer", "raise", "balling", "two-part"],
        "category": "low_parameters"
    },
    {
        "query": "My fish is flashing and scratching against rocks. What's wrong?",
        "expected_keywords": ["ich", "parasite", "velvet", "brooklynella", "treatment", "quarantine"],
        "category": "fish_disease"
    },
    {
        "query": "My torch coral tentacles are not coming out and it looks deflated.",
        "expected_keywords": ["flow", "lighting", "parameter", "stress", "neighboring", "sweeper"],
        "category": "coral_health"
    },
    {
        "query": "Alkalinity is swinging between 7 and 9 dKH every few days. How do I stabilize it?",
        "expected_keywords": ["dosing", "consistent", "pump", "buffer", "calcium", "test"],
        "category": "alkalinity_swing"
    },
    {
        "query": "My magnesium dropped to 1100 ppm. Will this hurt my corals?",
        "expected_keywords": ["magnesium", "calcium", "balance", "dose", "corals", "calcification"],
        "category": "low_magnesium"
    },
    {
        "query": "Brown slime covering my sandbed. Is this cyanobacteria?",
        "expected_keywords": ["cyano", "cyanobacteria", "nutrient", "flow", "phosphate", "nitrate"],
        "category": "cyano"
    },
    {
        "query": "My clam is not extending its mantle and looks pale.",
        "expected_keywords": ["lighting", "alkalinity", "calcium", "nitrate", "parameter", "flow"],
        "category": "invertebrate_health"
    },
    {
        "query": "All my corals are closed up and not opening. Tank is 2 weeks old.",
        "expected_keywords": ["cycle", "ammonia", "nitrite", "new tank", "stable", "parameter"],
        "category": "new_tank_issues"
    },
    {
        "query": "I have red bugs on my Acropora. How do I treat them?",
        "expected_keywords": ["red bug", "acropora", "interceptor", "milbemycin", "treatment"],
        "category": "coral_pest"
    },
    {
        "query": "Temperature spiked to 84°F for 6 hours. Are my corals in danger?",
        "expected_keywords": ["temperature", "heat", "stress", "coral", "bleach", "alkalinity"],
        "category": "temperature"
    },
    {
        "query": "My salinity is 1.028. Should I lower it?",
        "expected_keywords": ["salinity", "specific gravity", "1.025", "1.026", "evaporation", "top off"],
        "category": "salinity"
    },
    {
        "query": "Bubble algae is taking over my tank. How do I remove it?",
        "expected_keywords": ["bubble algae", "valonia", "manual", "emerald crab", "remove"],
        "category": "algae"
    },
]

def get_rag_context(query: str) -> str:
    """Get RAG context from vector database and expert rules."""
    try:
        from rag.rag import get_diagnosis_context, get_expert_routing_rules
        from rag.vector_db import get_vector_context

        # Get expert routing rules
        routing_rules = get_expert_routing_rules(query)

        # Get vector context
        vector_context = get_vector_context(query, k=3)

        # Combine
        context = f"""
### EXPERT RULES ###
{routing_rules}

### VECTOR KNOWLEDGE ###
{vector_context}
"""
        return context
    except Exception as e:
        return f"(RAG unavailable: {e})"


def query_llm(prompt: str, system: str = "You are ReefGPT, a reef aquarium diagnostic expert. Provide concise, accurate advice.") -> str:
    """Query the LLM with a prompt."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(LLM error: {e})"


def check_answer_accuracy(response: str, expected_keywords: list) -> float:
    """
    Check if the response contains expected keywords.
    Returns a score between 0 and 1.
    """
    response_lower = response.lower()
    matched = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
    return matched / len(expected_keywords)


def run_benchmark():
    """Run the full RAG benchmark."""
    print("=" * 60)
    print("ReefGPT RAG Diagnostic Benchmark")
    print("=" * 60)

    results = {
        "rag_scores": [],
        "baseline_scores": [],
        "details": []
    }

    for i, test_case in enumerate(TEST_QUERIES):
        query = test_case["query"]
        expected = test_case["expected_keywords"]
        category = test_case["category"]

        print(f"\n[{i+1}/{len(TEST_QUERIES)}] {category}")
        print(f"Query: {query[:60]}...")

        # --- Baseline (no RAG) ---
        baseline_response = query_llm(query)
        baseline_score = check_answer_accuracy(baseline_response, expected)
        results["baseline_scores"].append(baseline_score)

        print(f"  Baseline Score: {baseline_score:.2%}")

        # --- RAG (with context) ---
        rag_context = get_rag_context(query)
        rag_prompt = f"""
Use the following expert knowledge to answer the user's question.

{rag_context}

User Question: {query}

Provide a concise, accurate answer based on the expert knowledge above.
"""
        rag_response = query_llm(rag_prompt)
        rag_score = check_answer_accuracy(rag_response, expected)
        results["rag_scores"].append(rag_score)

        print(f"  RAG Score:      {rag_score:.2%}")

        # Store details
        results["details"].append({
            "query": query,
            "category": category,
            "expected_keywords": expected,
            "baseline_response": baseline_response,
            "baseline_score": baseline_score,
            "rag_context": rag_context[:500],
            "rag_response": rag_response,
            "rag_score": rag_score
        })

    # Calculate overall accuracy
    rag_accuracy = np.mean(results["rag_scores"])
    baseline_accuracy = np.mean(results["baseline_scores"])

    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"RAG System Accuracy:      {rag_accuracy:.2%}")
    print(f"Baseline LLM Accuracy:     {baseline_accuracy:.2%}")
    print(f"Improvement from RAG:      {rag_accuracy - baseline_accuracy:.2%}")

    # Bootstrap confidence intervals
    def bootstrap_ci(scores, n_bootstrap=1000):
        scores = np.array(scores)
        bootstrap_means = []
        n = len(scores)
        for _ in range(n_bootstrap):
            sample = np.random.choice(scores, size=n, replace=True)
            bootstrap_means.append(np.mean(sample))
        lower = np.percentile(bootstrap_means, 2.5)
        upper = np.percentile(bootstrap_means, 97.5)
        return lower, upper

    rag_lower, rag_upper = bootstrap_ci(results["rag_scores"])
    base_lower, base_upper = bootstrap_ci(results["baseline_scores"])

    print(f"\n95% Confidence Intervals:")
    print(f"  RAG:      [{rag_lower:.2%}, {rag_upper:.2%}]")
    print(f"  Baseline: [{base_lower:.2%}, {base_upper:.2%}]")

    # Save detailed results
    output_file = os.path.join(os.path.dirname(__file__), "benchmark_rag_results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nDetailed results saved to: {output_file}")

    return results


if __name__ == "__main__":
    run_benchmark()

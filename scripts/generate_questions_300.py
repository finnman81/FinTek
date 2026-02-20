"""
Generate 300 categorized evaluation questions.

Categories:
  - Exact spec lookup (torque, voltage, psi): 20% (60)
  - Step-by-step procedures: 25% (75)
  - Troubleshooting "symptom → cause": 20% (60)
  - Error code / part number queries: 15% (45)
  - Safety / warnings: 10% (30)
  - Multi-hop (combine 2 sections): 10% (30)

Usage:
  python scripts/generate_questions_300.py --output claw_manuals/eval_questions_300.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Template questions by category (you'll expand these based on your manuals)
QUESTION_TEMPLATES = {
    "spec_lookup": [
        # Exact specs: torque, voltage, pressure, temperature, flow rate
        "What is the maximum operating pressure for {model}?",
        "What voltage does {model} require?",
        "What is the torque specification for {model} bolts?",
        "What is the maximum flow rate for {model}?",
        "What is the operating temperature range for {model}?",
        "What is the minimum inlet pressure for {model}?",
        "What is the power consumption of {model}?",
        "What is the maximum psi rating for {model}?",
        "What is the electrical requirement for {model}?",
        "What are the dimensions of {model}?",
    ],
    "procedures": [
        # Step-by-step procedures
        "How do I install {model}?",
        "What are the steps to calibrate {model}?",
        "How do I program {model}?",
        "What is the procedure for replacing {part} on {model}?",
        "How do I perform maintenance on {model}?",
        "What are the setup steps for {model}?",
        "How do I configure {model}?",
        "What is the startup sequence for {model}?",
        "How do I troubleshoot {model}?",
        "What is the regeneration procedure for {model}?",
    ],
    "troubleshooting": [
        # Symptom → cause
        "{model} is making noise, what could be wrong?",
        "{model} is not starting, what should I check?",
        "{model} is leaking, what are possible causes?",
        "{model} shows low pressure, what could cause this?",
        "{model} is vibrating excessively, what should I investigate?",
        "{model} is not responding, what are troubleshooting steps?",
        "{model} error indicator is on, what does this mean?",
        "{model} is overheating, what could be the problem?",
        "{model} is not producing output, what should I check?",
        "{model} is cycling too frequently, what causes this?",
    ],
    "error_codes": [
        # Error codes and part numbers
        "What does error code {code} mean on {model}?",
        "What is part number {part} used for?",
        "What part do I need to replace {component} on {model}?",
        "What does fault code {code} indicate?",
        "What is the part number for {component} on {model}?",
        "How do I resolve error {code} on {model}?",
        "What component corresponds to part number {part}?",
        "What does alarm code {code} mean?",
        "What parts are needed for {model} maintenance?",
        "What is the replacement part for {part}?",
    ],
    "safety": [
        # Safety and warnings
        "What safety precautions should I take with {model}?",
        "What are the warning labels on {model}?",
        "What hazards are associated with {model}?",
        "What personal protective equipment is needed for {model}?",
        "What are the safety requirements for installing {model}?",
        "What should I do if {model} fails?",
        "What are the safety warnings in the {model} manual?",
        "What chemicals are hazardous in {model} operation?",
        "What are the electrical safety requirements for {model}?",
        "What are the lockout/tagout procedures for {model}?",
    ],
    "multi_hop": [
        # Multi-hop: combine information from multiple sections
        "What is the installation procedure and safety requirements for {model}?",
        "What are the specifications and troubleshooting steps for {model}?",
        "How do I install {model} and what error codes should I watch for?",
        "What are the maintenance procedures and part numbers for {model}?",
        "What are the operating specs and safety warnings for {model}?",
        "How do I configure {model} and what are common issues?",
        "What are the setup steps and calibration procedures for {model}?",
        "What are the electrical requirements and wiring diagrams for {model}?",
        "What are the flow rate specifications and troubleshooting for {model}?",
        "What are the installation requirements and error code meanings for {model}?",
    ],
}

# Models and components from your manuals (expand based on actual content)
MODELS = [
    "DOC submersible pump",
    "Lowara DOC pump",
    "Bell & Gossett e3-4",
    "Bell & Gossett e3-6",
    "Hach SC200 controller",
    "Siemens MAG 5000",
    "Siemens MAG 6000",
    "Fleck 5600",
    "Fleck 5600SXT",
    "Fleck 5800 LXT",
    "Fleck 5800 SXT",
    "Fleck 5800 XTR2",
    "Fleck 7000SXT",
    "Fleck 9000",
    "Fleck 9100",
    "Fleck SXT controller",
]

COMPONENTS = [
    "piston seals",
    "control valve",
    "brine tank",
    "resin bed",
    "motor",
    "impeller",
    "sensor",
    "transmitter",
    "controller",
    "valve assembly",
]

ERROR_CODES = ["E01", "E02", "E03", "E10", "E20", "F01", "F02", "ALARM1", "ALARM2"]
PART_NUMBERS = ["P-1234", "P-5678", "V-100", "V-200", "S-500", "M-300"]


def generate_questions() -> list[dict]:
    """Generate 300 categorized questions."""
    questions = []
    
    # Spec lookup: 60 questions
    for _ in range(60):
        template = random.choice(QUESTION_TEMPLATES["spec_lookup"])
        model = random.choice(MODELS)
        question = template.format(model=model)
        questions.append({
            "question": question,
            "category": "spec_lookup",
            "expected_sources": [model.lower().replace(" ", "_")],
            "expected_answer_contains": ["psi", "voltage", "pressure", "torque", "temperature", "flow"],
        })
    
    # Procedures: 75 questions
    for _ in range(75):
        template = random.choice(QUESTION_TEMPLATES["procedures"])
        model = random.choice(MODELS)
        part = random.choice(COMPONENTS) if "{part}" in template else ""
        question = template.format(model=model, part=part)
        questions.append({
            "question": question,
            "category": "procedures",
            "expected_sources": [model.lower().replace(" ", "_")],
            "expected_answer_contains": ["step", "procedure", "install", "calibrate", "program"],
        })
    
    # Troubleshooting: 60 questions
    for _ in range(60):
        template = random.choice(QUESTION_TEMPLATES["troubleshooting"])
        model = random.choice(MODELS)
        question = template.format(model=model)
        questions.append({
            "question": question,
            "category": "troubleshooting",
            "expected_sources": [model.lower().replace(" ", "_")],
            "expected_answer_contains": ["check", "cause", "problem", "issue", "troubleshoot"],
        })
    
    # Error codes / part numbers: 45 questions
    for _ in range(45):
        template = random.choice(QUESTION_TEMPLATES["error_codes"])
        model = random.choice(MODELS)
        code = random.choice(ERROR_CODES) if "{code}" in template else ""
        part = random.choice(PART_NUMBERS) if "{part}" in template else ""
        component = random.choice(COMPONENTS) if "{component}" in template else ""
        question = template.format(model=model, code=code, part=part, component=component)
        questions.append({
            "question": question,
            "category": "error_codes",
            "expected_sources": [model.lower().replace(" ", "_")],
            "expected_answer_contains": [code.lower(), part.lower()] if code or part else None,
        })
    
    # Safety: 30 questions
    for _ in range(30):
        template = random.choice(QUESTION_TEMPLATES["safety"])
        model = random.choice(MODELS)
        question = template.format(model=model)
        questions.append({
            "question": question,
            "category": "safety",
            "expected_sources": [model.lower().replace(" ", "_")],
            "expected_answer_contains": ["safety", "warning", "hazard", "precaution"],
        })
    
    # Multi-hop: 30 questions
    for _ in range(30):
        template = random.choice(QUESTION_TEMPLATES["multi_hop"])
        model = random.choice(MODELS)
        question = template.format(model=model)
        questions.append({
            "question": question,
            "category": "multi_hop",
            "expected_sources": [model.lower().replace(" ", "_")],
            "expected_answer_contains": None,  # Multi-hop may combine multiple concepts
        })
    
    # Shuffle for randomness
    random.shuffle(questions)
    
    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 300 categorized evaluation questions")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "claw_manuals" / "eval_questions_300.json")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    
    random.seed(args.seed)
    questions = generate_questions()
    
    # Verify distribution
    from collections import Counter
    categories = Counter(q["category"] for q in questions)
    print(f"Generated {len(questions)} questions:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count} ({100*count/len(questions):.1f}%)")
    
    # Save
    output_path = args.output if args.output.is_absolute() else PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)
    
    print(f"\nQuestions saved to: {output_path}")
    print("\nNote: You should manually review and refine these questions based on your actual manuals.")
    print("Update expected_sources to match actual document filenames.")


if __name__ == "__main__":
    main()

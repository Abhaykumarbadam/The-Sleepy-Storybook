"""
Create Opik Dataset from Real Stories

This script reads your actual generated stories from stories.json
and creates a proper dataset with inputs and outputs for evaluation.
"""

import os
import json
from pathlib import Path

# Set local Opik URL
os.environ["OPIK_URL_OVERRIDE"] = "http://localhost:8080"

print("🔧 Connecting to Opik...")

from opik import Opik

client = Opik(
    host="http://localhost:8080",
    project_name="Sleepy-Storybook"
)

print("✅ Connected to Opik Local Server")
print(f"📊 Project: Sleepy-Storybook")
print(f"🌐 UI: http://localhost:5173/default/projects/Sleepy-Storybook\n")

# Read stories from JSON file
stories_file = Path(__file__).parent / "data" / "stories.json"

print(f"📖 Reading stories from: {stories_file}")

try:
    with open(stories_file, 'r', encoding='utf-8') as f:
        all_stories = json.load(f)
    print(f"✅ Found {len(all_stories)} stories\n")
except Exception as e:
    print(f"❌ Error reading stories: {e}")
    exit(1)

# Filter out test stories and select good examples
good_stories = [
    story for story in all_stories 
    if story.get("title") != "Test Story" 
    and story.get("content") 
    and len(story.get("content", "")) > 100
    and story.get("prompt")
]

print(f"📝 Found {len(good_stories)} quality stories to add to dataset\n")

# Create dataset
dataset_name = "Real-Story-Examples"

print(f"📦 Creating dataset: {dataset_name}")

try:
    try:
        old_dataset = client.get_dataset(name=dataset_name)
        print(f"⚠️  Found existing dataset, will be replaced")
    except:
        pass
    
    dataset = client.create_dataset(name=dataset_name)
    print(f"✅ Created new dataset: {dataset_name}\n")
except Exception as e:
    print(f"❌ Error creating dataset: {e}")
    exit(1)

# Add stories to dataset (limit to top 10 for manageable dataset)
print(f"📥 Adding stories to dataset (max 10)...\n")

added_count = 0
max_stories = 10

for idx, story in enumerate(good_stories[:max_stories], 1):
    try:
        # Extract story details
        prompt = story.get("prompt", "")
        title = story.get("title", "")
        content = story.get("content", "")
        length_type = story.get("length_type", "medium")
        iterations = story.get("iterations", 1)
        final_score = story.get("final_score", {})
        
        # Determine age range
        age_range = story.get("age_range", "4-7")
        
        # Create dataset item with actual story
        dataset_item = {
            "input": prompt,
            "expected_output": {
                "title": title,
                "content": content,
                "length": length_type,
                "age_range": age_range,
                "quality_scores": {
                    "clarity": final_score.get("clarity", 0),
                    "moral_value": final_score.get("moralValue", 0),
                    "age_appropriateness": final_score.get("ageAppropriateness", 0),
                    "overall": final_score.get("score", 0)
                },
                "iterations_needed": iterations,
                "approved": final_score.get("approved", False)
            }
        }
        
        # Add to dataset
        dataset.insert([dataset_item])
        
        added_count += 1
        print(f"  ✓ [{idx}/{min(max_stories, len(good_stories))}] Added: '{title[:50]}...'")
        print(f"      Prompt: '{prompt[:60]}...'")
        print(f"      Length: {length_type} | Score: {final_score.get('score', 0)}/10 | Iterations: {iterations}")
        print()
        
    except Exception as e:
        print(f"  ✗ [{idx}] Failed to add story: {e}\n")

print("=" * 70)
print(f"✅ DATASET CREATED WITH REAL STORIES!")
print("=" * 70)

print(f"\n📊 Dataset Summary:")
print(f"  • Name: {dataset_name}")
print(f"  • Stories Added: {added_count}")
print(f"  • Source: {stories_file}")

print("\n🎯 What's in the Dataset:")
print("\n  Each item contains:")
print("  📝 Input:")
print("      • Original prompt used to generate the story")
print("\n  ✅ Expected Output:")
print("      • Actual generated story title")
print("      • Full story content")
print("      • Story length type (short/medium/long)")
print("      • Age range")
print("      • Quality scores (clarity, moral value, age appropriateness)")
print("      • Number of iterations needed")
print("      • Approval status")

print("\n🚀 Next Steps:")

print("\n1. Delete Old Dataset (if you want):")
print("   → Go to: http://localhost:5173/default/projects/Sleepy-Storybook")
print("   → Click 'Datasets'")
print("   → Find 'Story-Prompts-Dataset' and delete it")

print("\n2. View Your New Dataset:")
print("   → Click 'Datasets' tab")
print(f"   → Find '{dataset_name}'")
print("   → You'll see actual stories with their full content!")

print("\n3. Create an Experiment:")
print("   → Go to 'Experiments' section")
print("   → Click 'New Experiment'")
print(f"   → Select dataset: '{dataset_name}'")
print("   → Add evaluators:")
print("      • Hallucination (checks if content matches input)")
print("      • Moderation (checks age-appropriateness)")
print("      • Custom metrics (story quality, coherence, etc.)")

print("\n4. Evaluate New Stories Against Dataset:")
print("   → Generate new stories from your frontend")
print("   → Compare them against the examples in this dataset")
print("   → See how they measure up in quality!")

print("\n5. Track Improvements:")
print("   → Compare different model versions")
print("   → Test different prompting strategies")
print("   → Monitor quality trends over time")

print("\n📈 Use Cases:")
print("   • Regression testing: Ensure new changes don't reduce quality")
print("   • Benchmarking: Compare against your best stories")
print("   • Quality standards: Use high-scoring stories as reference")
print("   • Prompt optimization: Test which prompts produce better stories")

print("\n" + "=" * 70)
print(f"\n✨ Your dataset '{dataset_name}' is ready to use!")
print("   View it at: http://localhost:5173/default/projects/Sleepy-Storybook/datasets")
print("=" * 70)

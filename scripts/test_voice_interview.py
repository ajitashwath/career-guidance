"""
Verification script for Voice and Company Interview features.
Run with: python -m scripts.test_voice_interview
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import get_settings
from app.core.voice import generate_audio
from app.core.llm import get_company_questions_chain, format_profile_context

async def test_company_questions():
    print("Testing Company Question Generation...")
    
    # Mock profile context
    mock_context = {
        "profile": {
            "full_name": "Test User",
            "target_roles": ["Software Engineer"],
            "profile_tier": "Tier 1"
        },
        "skills": [
            {"skill_name": "Python", "proficiency_level": 5, "years_of_experience": 3},
            {"skill_name": "FastAPI", "proficiency_level": 4, "years_of_experience": 2}
        ]
    }
    
    formatted_context = format_profile_context(mock_context)
    chain = get_company_questions_chain()
    
    companies = ["Google", "Amazon"]
    target_role = "Senior Software Engineer"
    
    for company in companies:
        print(f"\n--- Generating questions for {company} ---")
        try:
            result = await chain.ainvoke({
                "profile_context": formatted_context,
                "company_name": company,
                "target_role": target_role
            })
            print(result)
        except Exception as e:
            print(f"Error: {e}")

def test_voice_generation():
    print("\nTesting Voice Generation...")
    
    text = "Hello! This is a test of the ElevenLabs voice integration. Good luck with your interview!"
    output_file = "test_voice.mp3"
    
    try:
        if not get_settings().elevenlabs_api_key:
            print("Skipping voice test: No ElevenLabs API key provided.")
            return

        audio_stream = generate_audio(text)
        
        with open(output_file, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)
                
        print(f"Success! Audio saved to {output_file}")
        
    except Exception as e:
        print(f"Error generating voice: {e}")

async def main():
    await test_company_questions()
    test_voice_generation()

if __name__ == "__main__":
    asyncio.run(main())

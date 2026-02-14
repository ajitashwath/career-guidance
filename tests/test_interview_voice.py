
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.intelligence.ai_service import generate_company_specific_questions, generate_voice_from_text
from app.core import voice

@pytest.mark.asyncio
async def test_generate_company_specific_questions():
    # Mock dependencies
    user_id = uuid4()
    target_role = "Software Engineer"
    companies = ["Google", "Amazon"]
    
    mock_context = {
        "profile": {"full_name": "Test User"},
        "skills": [],
        "education": [],
        "experience": [],
        "projects": []
    }
    
    mock_chain_result = {
        "company": "Google",
        "questions": [{"question": "Reverse a linked list", "type": "technical"}]
    }

    with patch("app.intelligence.ai_service.get_user_context", new_callable=AsyncMock) as mock_get_context, \
         patch("app.intelligence.ai_service.get_company_questions_chain") as mock_get_chain:
        
        mock_get_context.return_value = mock_context
        
        mock_chain = MagicMock()
        mock_chain.ainvoke = AsyncMock(return_value=mock_chain_result)
        mock_get_chain.return_value = mock_chain
        
        # execution
        results = await generate_company_specific_questions(user_id, target_role, companies)
        
        # verification
        assert results is not None
        assert "Google" in results
        assert "Amazon" in results
        assert results["Google"][0]["question"] == "Reverse a linked list"
        assert mock_chain.ainvoke.call_count == 2 # Once for each company

def test_generate_voice_from_text():
    text = "Hello world"
    mock_audio_stream = iter([b"chunk1", b"chunk2"])
    
    with patch("app.core.voice.get_elevenlabs_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.text_to_speech.convert.return_value = mock_audio_stream
        mock_get_client.return_value = mock_client
        
        # execution
        stream = generate_voice_from_text(text)
        
        # verification
        assert stream is not None
        chunks = list(stream)
        assert chunks == [b"chunk1", b"chunk2"]
        mock_client.text_to_speech.convert.assert_called_once()

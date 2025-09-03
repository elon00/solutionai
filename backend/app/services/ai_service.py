import time
import logging
from typing import Dict, Any, Optional
import openai
import anthropic
from ..config import settings


logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        openai.api_key = settings.openai_api_key
        self.anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    async def classify_ticket(self, ticket_text: str) -> Dict[str, Any]:
        """
        Classify ticket using AI with failover
        """
        start_time = time.time()

        prompt = f"""Classify this customer support ticket and provide a summary.

Ticket: {ticket_text}

Categories: bug, feature_request, billing_issue, other

Respond with valid JSON:
{{
    "label": "category_name",
    "confidence": 0.0-1.0,
    "summary": "brief summary of the issue"
}}

Strict JSON only."""

        try:
            # Try OpenAI first
            response = await openai.ChatCompletion.acreate(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )

            result = self._parse_ai_response(response.choices[0].message.content)
            processing_time = time.time() - start_time

            logger.info(f"OpenAI classification completed in {processing_time:.2f}s")
            return {**result, "processing_time": processing_time, "provider": "openai"}

        except Exception as e:
            logger.warning(f"OpenAI failed: {e}, trying Anthropic")

            try:
                # Fallback to Anthropic
                response = await self.anthropic_client.messages.create(
                    model=settings.anthropic_model,
                    max_tokens=200,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )

                result = self._parse_ai_response(response.content[0].text)
                processing_time = time.time() - start_time

                logger.info(f"Anthropic classification completed in {processing_time:.2f}s")
                return {**result, "processing_time": processing_time, "provider": "anthropic"}

            except Exception as e2:
                logger.error(f"Anthropic failed: {e2}")
                processing_time = time.time() - start_time

                return {
                    "label": "other",
                    "confidence": 0.0,
                    "summary": "Failed to classify ticket due to AI service unavailability",
                    "processing_time": processing_time,
                    "provider": "fallback"
                }

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response and validate format"""
        import json
        import re

        # Clean the response
        cleaned = re.sub(r'```json\s*|\s*```', '', response_text.strip())

        try:
            result = json.loads(cleaned)

            # Validate required fields
            if not all(key in result for key in ['label', 'confidence', 'summary']):
                raise ValueError("Missing required fields")

            # Validate label
            valid_labels = ['bug', 'feature_request', 'billing_issue', 'other']
            if result['label'] not in valid_labels:
                result['label'] = 'other'

            # Validate confidence
            result['confidence'] = max(0.0, min(1.0, float(result['confidence'])))

            return result

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            return {
                "label": "other",
                "confidence": 0.0,
                "summary": f"AI response parsing failed: {str(e)}"
            }


# Global instance
ai_service = AIService()
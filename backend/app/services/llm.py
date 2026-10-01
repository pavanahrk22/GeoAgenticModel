import asyncio
import logging
import httpx
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)

ROUTE_EXPLANATION_TEMPLATE = """
Based on current conditions, Route {rank} is the most suitable option.
It has an estimated arrival time of {eta} minutes covering {distance} km.
{reason}
This route avoids {incidents} active incident(s) in the area.
"""

async def generate_explanation(
    situation: dict,
    ranked_routes: list[dict],
    timeout: float = 4.0,
) -> str:
    settings = get_settings()
    provider = getattr(settings, "LLM_PROVIDER", "openai").lower()
    
    if not ranked_routes:
        return "No suitable routes found."
        
    best_route = ranked_routes[0]
    
    try:
        async with asyncio.timeout(timeout):
            if provider == "gemini":
                return await _generate_gemini(situation, ranked_routes, settings)
            elif provider == "openai":
                return await _generate_openai(situation, ranked_routes, settings)
            else:
                raise ValueError(f"Unknown provider: {provider}")
    except Exception as e:
        logger.warning(f"LLM explanation failed: {e}. Using fallback.")
        return ROUTE_EXPLANATION_TEMPLATE.format(
            rank=1,
            eta=round(best_route.get("duration", 0) / 60, 1),
            distance=round(best_route.get("distance", 0) / 1000, 1),
            reason="It offers a good balance of time and efficiency.",
            incidents=len(situation.get("incidents", []))
        ).strip()

def _build_prompt(situation: dict, ranked_routes: list[dict]) -> str:
    prompt = f"Situation: Current active incidents: {len(situation.get('incidents', []))}. "
    if ranked_routes:
        best = ranked_routes[0]
        prompt += f"Rank 1 route: {round(best.get('duration',0)/60, 1)} mins, {round(best.get('distance',0)/1000, 1)} km. "
    prompt += "Provide a 2-4 sentence explanation of why this route is suitable. Do not use the word 'safest', use 'suitable' or 'optimized'."
    return prompt

async def _generate_gemini(situation, ranked_routes, settings) -> str:
    # Simulating gemini call with httpx, or using google.generativeai if installed
    prompt = _build_prompt(situation, ranked_routes)
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

async def _generate_openai(situation, ranked_routes, settings) -> str:
    prompt = _build_prompt(situation, ranked_routes)
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": prompt}]
        })
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

from app.services.llm import generate_explanation, ROUTE_EXPLANATION_TEMPLATE

class ExplanationAgent:
    async def explain(self, situation: dict, ranked_routes: list[dict]) -> str:
        try:
            return await generate_explanation(situation, ranked_routes)
        except Exception:
            if not ranked_routes:
                return "No suitable routes."
            best = ranked_routes[0]
            return ROUTE_EXPLANATION_TEMPLATE.format(
                rank=1,
                eta=round(best.get("duration", 0)/60, 1),
                distance=round(best.get("distance", 0)/1000, 1),
                reason="Provides optimal timing and efficiency.",
                incidents=len(situation.get("incidents", []))
            )

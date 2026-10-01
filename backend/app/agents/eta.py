class ETAAgent:
    def calculate_eta(self, remaining_distance: float, segment_speeds: list[float], congestion_factors: list[float], baseline_eta: float) -> dict:
        # Simplified ETA calculation
        avg_speed = 40.0 * (1000.0 / 3600.0)  # 40km/h in m/s
        base_eta = remaining_distance / avg_speed if avg_speed > 0 else 0
        
        # Apply generic congestion
        avg_congestion = sum(congestion_factors) / len(congestion_factors) if congestion_factors else 1.0
        eta_seconds = base_eta * avg_congestion
        
        delay_percentage = ((eta_seconds - baseline_eta) / baseline_eta * 100) if baseline_eta > 0 else 0
        delayed = delay_percentage > 20.0
        
        return {
            "eta_seconds": eta_seconds,
            "delayed": delayed,
            "delay_percentage": delay_percentage,
            "baseline_comparison": baseline_eta
        }

"""Find a high-scoring itinerary within time, fee, and place-count limits."""
from recommendation import parse_visit_duration


def optimize_route(candidates, travel_times, available_time_hours, max_places, budget):
    if candidates is None or candidates.empty:
        return None
    candidates = candidates.reset_index(drop=True)
    n = len(candidates)
    max_places = min(max(1, int(max_places)), n)
    time_limit = max(0, float(available_time_hours) * 60)
    visit_times = [parse_visit_duration(v) for v in candidates["visit_duration"]]
    fees = [float(v or 0) for v in candidates["entry_fee"]]
    scores = [float(v or 0) for v in candidates["recommendation_score"]]

    # State key (mask, last_index) -> (elapsed_minutes, score, fee, previous_key)
    states = {}
    for i in range(n):
        try:
            travel = travel_times[0][i + 1]
        except (IndexError, TypeError):
            continue
        if travel is None:
            continue
        elapsed = float(travel) / 60 + visit_times[i]
        if elapsed <= time_limit and fees[i] <= budget:
            states[(1 << i, i)] = (elapsed, scores[i], fees[i], None)

    for size in range(1, max_places):
        current = [(key, value) for key, value in states.items() if key[0].bit_count() == size]
        for (mask, last), (elapsed, score, fee, _) in current:
            for nxt in range(n):
                if mask & (1 << nxt):
                    continue
                new_fee = fee + fees[nxt]
                if new_fee > budget:
                    continue
                try:
                    travel = travel_times[last + 1][nxt + 1]
                except (IndexError, TypeError):
                    continue
                if travel is None:
                    continue
                new_elapsed = elapsed + float(travel) / 60 + visit_times[nxt]
                if new_elapsed > time_limit:
                    continue
                key = (mask | (1 << nxt), nxt)
                candidate_state = (new_elapsed, score + scores[nxt], new_fee, (mask, last))
                old = states.get(key)
                # For a given subset and endpoint, keep the better score; break ties by less time.
                if old is None or candidate_state[1] > old[1] or (
                    candidate_state[1] == old[1] and candidate_state[0] < old[0]
                ):
                    states[key] = candidate_state

    feasible = [(key, state) for key, state in states.items() if key[0].bit_count() <= max_places]
    if not feasible:
        return None
    best_key, best_state = max(
        feasible,
        key=lambda item: (item[0][0].bit_count(), item[1][1], -item[1][0])
    )
    indices = []
    key = best_key
    while key is not None:
        indices.append(key[1])
        key = states[key][3]
    indices.reverse()
    return {
        "route": [candidates.iloc[i] for i in indices],
        "total_time_minutes": round(best_state[0]),
        "total_score": round(best_state[1], 2),
        "total_fee": round(best_state[2], 2),
    }

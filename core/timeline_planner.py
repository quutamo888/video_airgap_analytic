from typing import List, Dict, Any

def plan_cut_segments(
    raw_segments: List[Dict[str, float]],
    total_duration: float,
    speech_pad_sec: float = 0.15,
    min_silence_sec: float = 0.5
) -> Dict[str, Any]:
    """
    Takes raw VAD speech segments, applies padding (margins), merges overlapping
    speech segments, and identifies dead air intervals greater than min_silence_sec.
    Returns:
    {
        "speech_segments": [{"start": float, "end": float}],
        "dead_air_segments": [{"start": float, "end": float}]
    }
    """
    total_duration = round(total_duration, 3)
    if not raw_segments or total_duration <= 0:
        return {
            "speech_segments": [],
            "dead_air_segments": [{"start": 0.0, "end": total_duration}] if total_duration > 0 else []
        }

    # 1. Apply padding to raw segments
    padded = []
    for seg in raw_segments:
        s = max(0.0, seg["start"] - speech_pad_sec)
        e = min(total_duration, seg["end"] + speech_pad_sec)
        padded.append({"start": round(s, 3), "end": round(e, 3)})

    # 2. Merge overlapping or touching segments
    padded.sort(key=lambda x: x["start"])
    merged = [padded[0]]
    for cur in padded[1:]:
        prev = merged[-1]
        if cur["start"] <= prev["end"]:
            prev["end"] = max(prev["end"], cur["end"])
        else:
            merged.append(cur)

    # 3. Calculate silence intervals between speech segments
    silences = []
    current_time = 0.0

    for speech in list(merged):
        if speech["start"] > current_time:
            silence_len = speech["start"] - current_time
            if silence_len >= min_silence_sec:
                silences.append({"start": round(current_time, 3), "end": round(speech["start"], 3)})
            else:
                # Silence is too short to cut; absorb into previous speech segment
                idx = merged.index(speech)
                if idx > 0:
                    merged[idx - 1]["end"] = speech["start"]
        current_time = speech["end"]

    # Trailing silence
    if current_time < total_duration:
        trailing_len = total_duration - current_time
        if trailing_len >= min_silence_sec:
            silences.append({"start": round(current_time, 3), "end": round(total_duration, 3)})

    # Final pass to merge any touching speech segments after silence absorption
    final_speech = []
    for seg in merged:
        if not final_speech:
            final_speech.append(seg)
        else:
            if seg["start"] <= final_speech[-1]["end"]:
                final_speech[-1]["end"] = max(final_speech[-1]["end"], seg["end"])
            else:
                final_speech.append(seg)

    return {
        "speech_segments": final_speech,
        "dead_air_segments": silences
    }

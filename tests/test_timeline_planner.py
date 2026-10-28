from core.timeline_planner import plan_cut_segments

def test_empty_raw_segments():
    res = plan_cut_segments([], total_duration=10.0)
    assert len(res["speech_segments"]) == 0
    assert len(res["dead_air_segments"]) == 1
    assert res["dead_air_segments"][0] == {"start": 0.0, "end": 10.0}

def test_speech_padding_and_merging():
    # Two close speech segments: [1.0, 2.0] and [2.1, 3.0]
    # With pad 0.15, [0.85, 2.15] and [1.95, 3.15] overlap -> [0.85, 3.15]
    raw = [{"start": 1.0, "end": 2.0}, {"start": 2.1, "end": 3.0}]
    res = plan_cut_segments(raw, total_duration=5.0, speech_pad_sec=0.15, min_silence_sec=0.5)
    assert len(res["speech_segments"]) == 1
    assert res["speech_segments"][0]["start"] == 0.85
    assert res["speech_segments"][0]["end"] == 3.15
    assert len(res["dead_air_segments"]) == 2
    assert res["dead_air_segments"][0] == {"start": 0.0, "end": 0.85}
    assert res["dead_air_segments"][1] == {"start": 3.15, "end": 5.0}

def test_short_silence_absorption():
    # Two speech segments separated by 0.2s (less than min_silence_sec=0.5)
    # [1.0, 2.0] and [2.5, 3.5] -> padded [0.95, 2.05] and [2.45, 3.55], diff = 0.4s < 0.5s -> absorbed
    raw = [{"start": 1.0, "end": 2.0}, {"start": 2.4, "end": 3.5}]
    res = plan_cut_segments(raw, total_duration=5.0, speech_pad_sec=0.05, min_silence_sec=0.5)
    assert len(res["speech_segments"]) == 1
    assert res["speech_segments"][0]["start"] == 0.95
    assert res["speech_segments"][0]["end"] == 3.55

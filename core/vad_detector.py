import os
import urllib.request
import wave
import numpy as np
import onnxruntime as ort
from typing import List, Dict, Optional
from core.paths import get_resource_path

SILERO_VAD_ONNX_URL = "https://github.com/snakers4/silero-vad/raw/master/src/silero_vad/data/silero_vad.onnx"

class VadDetector:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            # First check bundled or local resources
            bundled_path = get_resource_path(os.path.join("core", "models", "silero_vad.onnx"))
            if os.path.exists(bundled_path):
                model_path = bundled_path
            else:
                models_dir = os.path.join(os.path.dirname(__file__), "models")
                os.makedirs(models_dir, exist_ok=True)
                model_path = os.path.join(models_dir, "silero_vad.onnx")
                if not os.path.exists(model_path):
                    try:
                        urllib.request.urlretrieve(SILERO_VAD_ONNX_URL, model_path)
                    except Exception as e:
                        raise RuntimeError(f"Could not download Silero VAD model: {e}")

        self.model_path = model_path
        opts = ort.SessionOptions()
        opts.inter_op_num_threads = 1
        opts.intra_op_num_threads = 1
        self.session = ort.InferenceSession(self.model_path, sess_options=opts, providers=["CPUExecutionProvider"])

        self.use_context = False
        self.context_size = 64
        self.reset_states()
        self._check_context_support()

    def reset_states(self):
        self._state = np.zeros((2, 1, 128), dtype=np.float32)
        self._context = np.zeros((1, self.context_size), dtype=np.float32)

    def _check_context_support(self):
        """
        Silero VAD v5 requires 64 context samples prepended to 512 audio chunk (total 576 samples).
        Probe the session to check if 576-sample input works.
        """
        try:
            dummy_x = np.zeros((1, 512 + self.context_size), dtype=np.float32)
            dummy_state = np.zeros((2, 1, 128), dtype=np.float32)
            sr_tensor = np.array(16000, dtype=np.int64)
            self.session.run(None, {
                "input": dummy_x,
                "state": dummy_state,
                "sr": sr_tensor
            })
            self.use_context = True
        except Exception:
            self.use_context = False
        self.reset_states()

    def _read_audio(self, wav_path: str) -> np.ndarray:
        with wave.open(wav_path, "rb") as wf:
            assert wf.getframerate() == 16000, f"Expected 16000Hz, got {wf.getframerate()}"
            assert wf.getnchannels() == 1, "Expected mono channel"
            assert wf.getsampwidth() == 2, "Expected 16-bit PCM"
            n_frames = wf.getnframes()
            audio_bytes = wf.readframes(n_frames)
            audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            return audio

    def detect_speech_segments(
        self,
        wav_path: str,
        threshold: float = 0.5,
        window_size_samples: int = 512
    ) -> List[Dict[str, float]]:
        """
        Runs Silero VAD on the audio file and returns a list of speech intervals:
        [{'start': float, 'end': float}] in seconds.
        """
        self.reset_states()
        audio = self._read_audio(wav_path)
        sample_rate = 16000
        sr_tensor = np.array(sample_rate, dtype=np.int64)

        speech_probs = []
        for i in range(0, len(audio) - window_size_samples + 1, window_size_samples):
            chunk = audio[i : i + window_size_samples]
            x = np.expand_dims(chunk, 0)

            if self.use_context:
                x_input = np.concatenate([self._context, x], axis=1)
            else:
                x_input = x

            ort_inputs = {
                "input": x_input,
                "state": self._state,
                "sr": sr_tensor
            }
            ort_outs = self.session.run(None, ort_inputs)
            prob, self._state = ort_outs[0], ort_outs[1]

            if self.use_context:
                self._context = x_input[:, -self.context_size:]

            speech_probs.append((i / sample_rate, float(prob[0][0])))

        segments = []
        in_speech = False
        start_time = 0.0

        for timestamp, prob in speech_probs:
            if prob >= threshold and not in_speech:
                in_speech = True
                start_time = timestamp
            elif prob < threshold and in_speech:
                in_speech = False
                segments.append({"start": round(start_time, 3), "end": round(timestamp, 3)})

        if in_speech:
            total_duration = len(audio) / sample_rate
            segments.append({"start": round(start_time, 3), "end": round(total_duration, 3)})

        return segments

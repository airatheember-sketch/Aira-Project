import asyncio
import numpy as np
from openwakeword.model import Model

# ── Load openWakeWord model once at startup ───────────────────────────────────
# Uses the built-in "hey_jarvis" model as base — closest to "hey aira" phonetically
# In Phase 9 we train a custom "hey_aira" model
_wake_model = None
WAKE_WORDS = ["hey jarvis", "jarvis"]  # swap with custom "hey_aira" model in Phase 9
DETECTION_THRESHOLD = 0.5              # confidence threshold — tune if too sensitive


def get_wake_model():
    global _wake_model
    if _wake_model is None:
        print("[Wake] Loading openWakeWord model...")
        _wake_model = Model(
            wakeword_models=["hey_jarvis"],  # built-in model, phonetically close to "hey aira"
            inference_framework="onnx"
        )
        print("[Wake] Wake word model loaded.")
    return _wake_model


async def process_audio_chunk(audio_chunk: bytes) -> bool:
    """
    Process a raw PCM audio chunk through openWakeWord.
    
    Args:
        audio_chunk: Raw PCM audio bytes
                     Expected: 16kHz, 16-bit, mono (standard browser AudioWorklet output)
    
    Returns:
        True if wake word detected, False otherwise
    """
    model = get_wake_model()

    # Convert raw bytes to numpy int16 array, then normalize to float32
    audio_data = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32768.0

    # Run inference — returns dict of {wakeword: confidence_score}
    predictions = model.predict(audio_data)

    # Check if any wake word crossed the threshold
    for wakeword, score in predictions.items():
        if score >= DETECTION_THRESHOLD:
            print(f"[Wake] Detected '{wakeword}' with confidence {score:.2f}")
            return True

    return False


def reset_wake_model():
    """Reset model state between detections to avoid false positives."""
    model = get_wake_model()
    model.reset()
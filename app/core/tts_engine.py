"""Thread-safe wrapper around the VoxCPM2 model."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable, Iterator, Optional

import numpy as np

from app.utils.constants import DEFAULT_CFG, DEFAULT_STEPS, FALLBACK_SAMPLE_RATE

logger = logging.getLogger(__name__)


class TTSEngine:
    """
    Thread-safe wrapper for the VoxCPM2 TTS model.

    All ``generate*`` methods acquire an internal lock so concurrent calls
    from multiple threads are serialised.  Long-running calls should therefore
    be executed from a dedicated *worker* thread (never the GUI main thread).

    Example::

        engine = TTSEngine()
        engine.load_model(progress_callback=print)
        wav = engine.generate(text="Hello world")
    """

    def __init__(self) -> None:
        self._model: Optional[object] = None  # voxcpm.VoxCPM
        self._lock = threading.Lock()
        self._is_loading: bool = False

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    @property
    def is_loading(self) -> bool:
        return self._is_loading

    @property
    def sample_rate(self) -> int:
        """Output sample rate reported by the model (default 48 000 Hz)."""
        if self._model is not None:
            try:
                return int(self._model.tts_model.sample_rate)  # type: ignore[attr-defined]
            except AttributeError:
                pass
        return FALLBACK_SAMPLE_RATE

    # ── Model lifecycle ───────────────────────────────────────────────────────

    def load_model(
        self,
        model_name: str = "openbmb/VoxCPM2",
        load_denoiser: bool = False,
        cache_dir: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """
        Download (if necessary) and load the VoxCPM2 model.

        This is a **blocking** call; run it from a worker thread.

        Args:
            model_name:       HuggingFace model id or local path.
            load_denoiser:    Whether to load the optional denoiser head.
            cache_dir:        Directory to cache downloaded model files.
                              If None, uses the HuggingFace default cache.
            progress_callback: Called with status messages during loading.

        Raises:
            RuntimeError: If the model is already loading, ``voxcpm`` is not
                          installed, or loading fails for any reason.
        """
        if self._is_loading:
            raise RuntimeError("Model loading is already in progress.")
        if self.is_loaded:
            raise RuntimeError(
                "A model is already loaded.  Call unload_model() first."
            )

        self._is_loading = True
        try:
            self._notify(progress_callback, "Importing voxcpm …")
            try:
                from voxcpm import VoxCPM  # type: ignore[import]
            except ImportError as exc:
                raise RuntimeError(
                    "Package 'voxcpm' is not installed.  "
                    "Run:  pip install voxcpm"
                ) from exc

            self._notify(
                progress_callback, f"Loading {model_name} … (may download ~8 GB on first run)"
            )

            pretrained_kwargs: dict = {
                "load_denoiser": load_denoiser,
                # optimize=False disables torch.compile and the short-sequence
                # warmup call that crashes scaled_dot_product_attention.
                "optimize": False,
            }
            if cache_dir:
                resolved = str(Path(cache_dir).resolve())
                Path(resolved).mkdir(parents=True, exist_ok=True)
                pretrained_kwargs["cache_dir"] = resolved
                logger.info("Model cache directory: %s", resolved)

            model = VoxCPM.from_pretrained(
                model_name,
                **pretrained_kwargs,
            )

            with self._lock:
                self._model = model

            self._notify(
                progress_callback,
                f"✓ Model ready  |  SR = {self.sample_rate} Hz",
            )
            logger.info("VoxCPM2 loaded: %s  SR=%d", model_name, self.sample_rate)

        except RuntimeError:
            raise
        except Exception as exc:
            logger.exception("Failed to load %s", model_name)
            raise RuntimeError(f"Model load failed: {exc}") from exc
        finally:
            self._is_loading = False

    def unload_model(self) -> None:
        """Release model and free GPU memory."""
        with self._lock:
            if self._model is None:
                return
            try:
                del self._model
                self._model = None
                try:
                    import torch  # type: ignore[import]
                    torch.cuda.empty_cache()
                    logger.info("CUDA cache cleared after model unload.")
                except Exception:  # noqa: BLE001
                    pass
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error during model unload: %s", exc)
                self._model = None

    # ── Generation ────────────────────────────────────────────────────────────

    def generate(
        self,
        text: str,
        reference_wav_path: Optional[str] = None,
        prompt_wav_path: Optional[str] = None,
        prompt_text: Optional[str] = None,
        cfg_value: float = DEFAULT_CFG,
        inference_timesteps: int = DEFAULT_STEPS,
    ) -> np.ndarray:
        """
        Generate audio for a text string (all cloning modes supported).

        **Voice Design**: embed description in parentheses at the start of
        *text*, e.g. ``"(gentle female voice)Hello world"``

        **Controllable Cloning**: supply *reference_wav_path*; optionally
        embed style guidance in *text* parentheses.

        **Ultimate Cloning**: supply *reference_wav_path*, *prompt_wav_path*,
        and *prompt_text* (transcript of the prompt audio).

        Args:
            text:                  Text to synthesise.
            reference_wav_path:    Path to reference audio for voice style.
            prompt_wav_path:       Path to prompt audio (Ultimate Cloning).
            prompt_text:           Transcript of prompt audio.
            cfg_value:             Classifier-free guidance scale (default 2.0).
            inference_timesteps:   Diffusion steps (default 10).

        Returns:
            float32 numpy array of shape ``(N,)`` at ``self.sample_rate`` Hz.

        Raises:
            RuntimeError:  Model not loaded, or generation error.
            ValueError:    Empty text.
            FileNotFoundError: Audio path does not exist.
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("Text to synthesise must not be empty.")

        with self._lock:
            if self._model is None:
                raise RuntimeError(
                    "Model is not loaded.  Open Settings and click 'Load Model'."
                )

            kwargs: dict = {
                "text": text,
                "cfg_value": float(cfg_value),
                "inference_timesteps": int(inference_timesteps),
            }

            if reference_wav_path:
                _assert_file(reference_wav_path, "Reference audio")
                kwargs["reference_wav_path"] = str(reference_wav_path)

            if prompt_wav_path:
                _assert_file(prompt_wav_path, "Prompt audio")
                kwargs["prompt_wav_path"] = str(prompt_wav_path)

            if prompt_text:
                kwargs["prompt_text"] = prompt_text.strip()

            try:
                wav: np.ndarray = self._model.generate(**kwargs)  # type: ignore[attr-defined]
            except Exception as exc:
                logger.exception("generate() failed")
                raise RuntimeError(f"Generation failed: {exc}") from exc

        return wav.astype(np.float32) if wav.dtype != np.float32 else wav

    def generate_streaming(
        self,
        text: str,
        reference_wav_path: Optional[str] = None,
        cfg_value: float = DEFAULT_CFG,
        inference_timesteps: int = DEFAULT_STEPS,
    ) -> Iterator[np.ndarray]:
        """
        Streaming generation — yields float32 audio chunks as they are produced.

        The model lock is held for the duration of the generator; fully
        consume or close the generator before calling ``generate()`` again.

        Yields:
            float32 numpy arrays (audio chunks).

        Raises:
            RuntimeError:  Model not loaded.
            ValueError:    Empty text.
        """
        text = (text or "").strip()
        if not text:
            raise ValueError("Text must not be empty.")

        with self._lock:
            if self._model is None:
                raise RuntimeError("Model is not loaded.")

            kwargs: dict = {
                "text": text,
                "cfg_value": float(cfg_value),
                "inference_timesteps": int(inference_timesteps),
            }

            if reference_wav_path:
                _assert_file(reference_wav_path, "Reference audio")
                kwargs["reference_wav_path"] = str(reference_wav_path)

            try:
                yield from self._model.generate_streaming(**kwargs)  # type: ignore[attr-defined]
            except Exception as exc:
                logger.exception("generate_streaming() failed")
                raise RuntimeError(f"Streaming generation failed: {exc}") from exc

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _notify(
        callback: Optional[Callable[[str], None]], msg: str
    ) -> None:
        if callback:
            try:
                callback(msg)
            except Exception:  # noqa: BLE001
                pass


# ── Module-level helpers ──────────────────────────────────────────────────────


def _assert_file(path: str, label: str) -> None:
    if not Path(path).exists():
        raise FileNotFoundError(f"{label} not found: {path}")

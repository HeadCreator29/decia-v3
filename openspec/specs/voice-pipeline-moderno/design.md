# Design: Modern Voice Pipeline for DECIA v3

## API Contracts

### VADProcessor
```python
class VADProcessor:
    def __init__(
        self,
        threshold: float = 0.5,
        min_speech_ms: int = 250,
        min_silence_ms: int = 100,
        model_path: str = "models/silero_vad.onnx",
        sample_rate: int = 16000,
        fallback_enabled: bool = True,
    ): ...
    
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    
    def process_frame(self, frame: np.ndarray) -> VADResult:
        """Process 512-sample frame @ 16kHz. Sync, <5ms."""
        ...
    
    @property
    def speech_started(self) -> asyncio.Event: ...
    @property
    def speech_ended(self) -> asyncio.Event: ...

@dataclass
class VADResult:
    probability: float
    is_speech: bool
    speech_start: bool
    speech_end: bool
```

### STTProcessor
```python
class STTProcessor:
    def __init__(
        self,
        model_size: str = "small",
        language: str = "es",
        beam_size: int = 5,
        compute_type: str = "int8",
        device: str = "cpu",
    ): ...
    
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    
    async def transcribe_stream(
        self,
        audio_buffer: np.ndarray,
        on_partial: Callable[[str], Awaitable[None]],
        on_final: Callable[[str], Awaitable[None]],
    ) -> None:
        """Stream transcription. Calls on_partial for each chunk, on_final at end."""
        ...

@dataclass
class STTResult:
    text: str
    is_partial: bool
    confidence: float
    language: str
```

### TTSProcessor
```python
class TTSProcessor:
    def __init__(
        self,
        voice_id: str = "es_ES-carlfm-x_low",
        speed: float = 1.0,
        sample_rate: int = 22050,
        model_dir: str = "models",
        fallback_enabled: bool = True,
    ): ...
    
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    
    async def synthesize_stream(
        self,
        text_stream: AsyncIterator[str],
        on_chunk: Callable[[np.ndarray], Awaitable[None]],
    ) -> None:
        """Stream synthesis. Calls on_chunk for each audio chunk."""
        ...
    
    def stop_current(self) -> None:
        ...

@dataclass
class TTSChunk:
    audio: np.ndarray
    is_final: bool
    text_source: str
```

### Pipeline (Orchestrator)
```python
class VoicePipeline:
    class State(Enum):
        LISTENING = "listening"
        CAPTURING = "capturing"
        PROCESSING = "processing"
        THINKING = "thinking"
        SPEAKING = "speaking"
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        intent_layer: Optional[IntentLayer] = None,
        llm_client: Optional[Callable[[str], Awaitable[str]]] = None,
    ): ...
    
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    
    @property
    def state(self) -> State: ...
    @property
    def metrics(self) -> PipelineMetrics: ...
    
    # Event callbacks
    on_transcription_partial: Optional[Callable[[str], Awaitable[None]]] = None
    on_transcription_final: Optional[Callable[[str], Awaitable[None]]] = None
    on_intent_classified: Optional[Callable[[ClassifyResult], Awaitable[None]]] = None
    on_response_start: Optional[Callable[[str], Awaitable[None]]] = None
    on_response_complete: Optional[Callable[[str], Awaitable[None]]] = None
    on_barge_in: Optional[Callable[[], Awaitable[None]]] = None
    on_error: Optional[Callable[[Exception], Awaitable[None]]] = None
    on_state_change: Optional[Callable[[State, State], Awaitable[None]]] = None
```

---

## Threading Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     ASYNCIO EVENT LOOP                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Pipeline    │  │ STTProcessor│  │ TTSProcessor│              │
│  │ Orchestrator│  │ (async)     │  │ (async)     │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              ASYNCIO QUEUES (thread-safe)               │    │
│  │  audio_frames → vad_results → stt_partials → stt_final  │    │
│  │  llm_tokens → tts_chunks → audio_chunks                 │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ thread-safe queue (janus.Queue)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AUDIO CALLBACK THREAD                       │
│  ┌─────────────────────┐         ┌─────────────────────┐       │
│  │ sounddevice         │         │ sounddevice         │       │
│  │ InputStream         │         │ OutputStream        │       │
│  │ (callback)          │         │ (callback)          │       │
│  └──────────┬──────────┘         └──────────┬──────────┘       │
│             │                               │                  │
│             ▼                               ▼                  │
│      RingBuffer (pre-roll)            Audio Queue (chunks)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Strategy

| Stage | Failure Mode | Handling |
|-------|--------------|----------|
| VAD | Model load fail | Fallback to WebRTC VAD (if enabled), else raise |
| VAD | Inference error | Log, continue with last known state |
| STT | Model load fail | Raise (critical) |
| STT | Transcription error | Log, return empty final, continue |
| STT | OOM | Reduce beam_size, retry once |
| TTS (Piper) | Model load fail | Fallback to pyttsx3 (if enabled) |
| TTS (Piper) | Synthesis error mid-stream | Log, switch to pyttsx3 for remainder |
| TTS (pyttsx3) | Failure | Log, silent skip utterance |
| AudioInput | Device error | Log, retry with default device |
| AudioOutput | Underrun | Increment metric, continue |
| AudioOutput | Device error | Log, stop pipeline |
| LLM (Ollama) | Connection error | Retry 3x with backoff, then error event |
| LLM (Ollama) | Timeout | Cancel, return partial, error event |
| Pipeline | Any stage crash | Log, transition to LISTENING, error callback |

**Retry Policy:**
- Transient (network, temp OOM): 3 retries, exponential backoff (100ms, 500ms, 2s)
- Permanent (model missing, device gone): No retry, fail fast

---

## Benchmark Harness Design

```python
class BenchmarkHarness:
    def __init__(self, pipeline: VoicePipeline, config: BenchmarkConfig): ...
    
    async def run_latency_benchmark(
        self,
        num_samples: int = 1000,
        utterances: List[str] = None,
    ) -> LatencyReport: ...
    
    async def run_barge_in_benchmark(
        self,
        num_interruptions: int = 100,
        trigger_at_ms: List[int] = None,
    ) -> BargeInReport: ...
    
    async def run_stability_test(
        self,
        duration_minutes: int = 10,
        utterances: List[str] = None,
    ) -> StabilityReport: ...
    
    async def run_vad_robustness_test(
        self,
        noise_file: str,
        duration_minutes: int = 10,
    ) -> VADRobustnessReport: ...

@dataclass
class LatencyReport:
    p50_ms: float
    p95_ms: float
    p99_ms: float
    breakdown: Dict[str, float]  # vad, stt, intent, llm, tts, audio
    passed: bool  # p95 < 800ms
```

---

## File Structure

```
app/services/
├── voice_pipeline/
│   ├── __init__.py
│   ├── pipeline.py           # VoicePipeline orchestrator
│   ├── vad_processor.py      # Silero VAD + WebRTC fallback
│   ├── stt_processor.py      # Streaming faster-whisper
│   ├── tts_processor.py      # Piper + pyttsx3 fallback
│   ├── audio_input.py        # sounddevice InputStream callback
│   ├── audio_output.py       # sounddevice OutputStream callback
│   ├── ring_buffer.py        # Thread-safe ring buffer
│   ├── config.py             # PipelineConfig, env loading
│   ├── metrics.py            # PipelineMetrics, benchmarking
│   └── exceptions.py         # Custom exceptions
├── voice.py                  # LEGACY - keep for backward compat
└── speaker.py                # LEGACY - keep for fallback
```

---

## Migration Strategy

1. **New pipeline** in `voice_pipeline/` (no changes to existing code)
2. **Feature flag**: `DECIA_VOICE_ENABLED=1` to enable
3. **Legacy path**: `voice.py` + `speaker.py` unchanged (fallback)
3. **Gradual rollout**: Test with flag, then make default
4. **Remove legacy**: After 2 releases stable

---

## Testing Strategy

| Layer | Approach |
|-------|----------|
| Unit | Mock audio, test each processor in isolation |
| Integration | Pipeline with mocked LLM/STT/TTS |
| Contract | Callback signatures, event ordering |
| Property-based | State machine transitions (hypothesis) |
| Benchmark | CI gate: p95 < 800ms, barge-in < 300ms |
| Stress | 10min conversation, noise injection |
| Regression | All 354 existing tests pass |

---

## Dependencies (new)

```toml
# pyproject.toml additions
[project.optional-dependencies]
voice-pipeline = [
    "silero-vad>=1.0",
    "piper-tts>=1.2",
    "janus>=1.0",
    "numpy>=1.24",
    "sounddevice>=0.4",
    "faster-whisper>=1.0",
    "soundfile>=0.12",
    "scipy>=1.10",
]
```

---

## Next Steps

1. **Tasks phase** (sdd-tasks): Break into 6 implementation phases
2. **Implementation** (sdd-apply): Phase 1 → 6
3. **Verification** (sdd-verify): Acceptance tests + CI benchmarks
4. **Archive** (sdd-archive): Delta spec sync
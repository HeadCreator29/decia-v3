# Tasks: Modern Voice Pipeline for DECIA v3

## Phase 1: Foundation (Week 1) — Core Infrastructure

### Task 1.1: Project Setup & Dependencies
- [ ] Add voice-pipeline optional dependencies to pyproject.toml:
  - silero-vad (or torch + onnxruntime for export)
  - piper-tts
  - janus (thread-safe queues)
- [ ] Create `app/services/voice_pipeline/` package with `__init__.py`
- [ ] Create `.env.example` with all config variables

### Task 1.2: RingBuffer Implementation
- [ ] Implement `RingBuffer` class in `ring_buffer.py`:
  - Thread-safe circular buffer (numpy backend)
  - Methods: write(), read(), get_latest(), clear(), available_samples
  - Configurable capacity (samples), channels, dtype
  - Unit tests: concurrent write/read, overflow, wrap-around

### Task 1.3: AudioInput Implementation
- [ ] Implement `AudioInput` in `audio_input.py`:
  - sounddevice InputStream with callback mode
  - Configurable device_id, sample_rate, blocksize, pre_roll_ms
  - Callback pushes frames to asyncio.Queue via janus.Queue
  - RingBuffer integration for pre-roll
  - start()/stop() lifecycle
  - Unit tests: callback timing, queue flow, pre-roll capture

### Task 1.4: AudioOutput Implementation
- [ ] Implement `AudioOutput` in `audio_output.py`:
  - sounddevice OutputStream with callback mode
  - Configurable device_id, sample_rate, blocksize
  - Async write() with backpressure (asyncio.Queue maxsize)
  - stop_immediate() for barge-in (clear queue, silence DAC)
  - Buffer underrun counter metric
  - Unit tests: write/stop, underrun detection, callback timing

### Task 1.5: RingBuffer + Audio Integration Tests
- [ ] Integration test: AudioInput → RingBuffer → AudioOutput loopback
- [ ] Verify pre-roll capture and playback
- [ ] Stress test: 10min continuous, no memory leaks

---

## Phase 2: VAD Processor (Week 1-2)

### Task 2.1: Silero VAD Processor
- [ ] Implement `VADProcessor` in `vad_processor.py`:
  - Load Silero ONNX model (torch.hub or onnxruntime)
  - process_frame(frame: np.ndarray) → VADResult (sync, <5ms)
  - Configurable threshold, min_speech_ms, min_silence_ms
  - speech_started / speech_ended asyncio.Event properties
  - Warmup inference on start()
  - Fallback to WebRTC VAD if ONNX load fails

### Task 2.2: VAD Unit Tests
- [ ] Test VADResult fields on known speech/silence samples
- [ ] Test speech_start/speech_end events on synthetic audio
- [ ] Benchmark: <5ms per frame on CPU
- [ ] Test threshold tuning (ROC curve on validation set)

### Task 2.3: WebRTC VAD Fallback
- [ ] Implement `WebRTCVADProcessor` with same interface
- [ ] webrtcvad library, frame-based (10/20/30ms)
- [ ] Auto-fallback in VADProcessor if Silero fails
- [ ] Config flag: `vad_fallback_enabled`

### Task 2.4: VAD Integration with AudioInput
- [ ] Connect AudioInput.frames → VADProcessor → vad_results queue
- [ ] Test end-to-end: microphone → VAD → speech_start/end events
- [ ] Verify pre-roll buffer captures speech before speech_start

---

## Phase 3: Streaming STT (Week 2)

### Task 3.1: STTProcessor with Streaming
- [ ] Implement `STTProcessor` in `stt_processor.py`:
  - faster-whisper with `stream=True`
  - transcribe_stream(audio_buffer, on_partial, on_final)
  - Model: small, int8, beam_size=5, language=es
  - Handle segment boundaries (no word splitting)
  - Config: model_size, language, beam_size, compute_type

### Task 3.2: STT Streaming Integration
- [ ] Connect VAD speech_end → STTProcessor.transcribe_stream()
- [ ] on_partial → transcription_partial queue
- [ ] on_final → transcription_final queue
- [ ] Handle overlapping segments gracefully

### Task 3.3: STT Unit & Integration Tests
- [ ] Unit test: partial → final progression on known audio
- [ ] Test segment boundary handling (no word splitting)
- [ ] Integration: VAD speech_end → STT → partial → final
- [ ] Benchmark: latency vs accuracy tradeoff

---

## Phase 4: Streaming TTS + Piper (Week 2-3)

### Task 4.1: Piper TTS Processor
- [ ] Implement `TTSProcessor` in `tts_processor.py`:
  - Load Piper voice (es_ES-carlfm-x_low)
  - synthesize_stream(text_stream, on_chunk)
  - Sentence chunking: split on .!? + min 10 chars
  - Piper streaming synthesis → on_chunk(PCM 22kHz float32)
  - stop_current() for barge-in
  - Config: voice_id, speed, chunk_strategy

### Task 4.2: pyttsx3 Fallback TTS
- [ ] Implement `Pyttsx3TTS` with same interface
- [ ] Load on demand (fallback only)
- [ ] synthesize_stream() wraps pyttsx3 (non-streaming but chunked)
- [ ] stop_current() support

### Task 4.3: Fallback Chain Logic
- [ ] TTSProcessor tries Piper first
- [ ] On any error: log, switch to pyttsx3 for current utterance
- [ ] pyttsx3 failure → log, silent skip
- [ ] Next utterance retries Piper
- [ ] Config: `tts_fallback_enabled`

### Task 4.4: TTS Unit & Integration Tests
- [ ] Unit: Piper loads, synthesizes chunks, stop_current()
- [ ] Unit: Fallback triggers on simulated Piper failure
- [ ] Integration: text_stream → TTS → audio_chunks queue
- [ ] Benchmark: first chunk < 100ms after first text

---

## Phase 5: Pipeline Orchestration (Week 3)

### Task 5.1: State Machine
- [ ] Implement `PipelineStateMachine` in `state_machine.py`:
  - States: LISTENING, CAPTURING, PROCESSING, THINKING, SPEAKING
  - Transitions triggered by events (VAD, STT, TTS, barge-in)
  - Invalid transition protection
  - State change callbacks

### Task 5.2: VoicePipeline Orchestrator
- [ ] Implement `VoicePipeline` in `pipeline.py`:
  - Compose all processors (VAD, STT, TTS, AudioInput, AudioOutput)
  - IntentLayer + OllamaClient integration
  - Queue wiring: frames → VAD → STT → Intent → LLM → TTS → AudioOutput
  - Barge-in detection: VAD during SPEAKING → interrupt
  - Pre-roll preservation on barge-in
  - Event callbacks (on_transcription_partial, on_barge_in, etc.)
  - Metrics collection (PipelineMetrics)

### Task 5.3: Barge-In Implementation
- [ ] VAD monitoring during SPEAKING state
- [ ] On speech_start during SPEAKING:
  - AudioOutput.stop_immediate()
  - Flush all queues (STT, LLM, TTS)
  - Preserve pre-roll buffer
  - Transition to CAPTURING
  - Resume from preserved buffer
- [ ] Barge-in detection < 300ms

### Task 5.4: Pipeline Integration Tests
- [ ] Test full pipeline: listen → transcribe → intent → LLM → TTS → audio
- [ ] Test state transitions: LISTENING → CAPTURING → ... → SPEAKING
- [ ] Test barge-in at multiple points in SPEAKING
- [ ] Test pre-roll preservation on barge-in
- [ ] Test graceful shutdown (drain queues, stop audio)

---

## Phase 6: Integration, Benchmarks & Polish (Week 3-4)

### Task 6.1: Configuration System
- [ ] Implement `PipelineConfig` in `config.py`:
  - Load from .env (dotenv) + YAML override
  - Validation with defaults
  - All sections: VAD, STT, TTS, Audio, Pipeline, Fallback
  - Feature flag: `DECIA_VOICE_ENABLED`

### Task 6.2: Main Loop Migration
- [ ] Modify `app/main.py`:
  - Feature flag check: `DECIA_VOICE_ENABLED=1`
  - If enabled: `VoicePipeline.start()` + event loop
  - Else: legacy `listen()` → `think()` → `speak()`
  - Preserve ConversationContext, speech_corrections

### Task 6.3: Benchmark Harness
- [ ] Implement `BenchmarkHarness` in `metrics.py`:
  - run_latency_benchmark(num_samples=1000) → LatencyReport
  - run_barge_in_benchmark(num_interruptions=100) → BargeInReport
  - run_stability_test(duration_minutes=10) → StabilityReport
  - run_vad_robustness_test(noise_file, duration_minutes=10) → VADReport
  - CI gate: p95 < 800ms, barge-in < 300ms

### Task 6.4: Acceptance Test Suite
- [ ] Create `tests/test_voice_pipeline.py`:
  - Test Scenario 1: Basic turn < 800ms
  - Test Scenario 2: Barge-in < 300ms
  - Test Scenario 3: 10min stability
  - Test Scenario 4: VAD noise robustness
  - Test Scenario 5: TTS fallback
  - Test Scenario 6: Rapid interruptions

### Task 6.5: CI Integration & Regression
- [ ] Add benchmark to CI pipeline (gate on p95 < 800ms)
- [ ] Verify all 354 existing tests pass
- [ ] Add voice pipeline tests to test suite
- [ ] Documentation: README for voice_pipeline, config guide

### Task 6.6: Polish & Documentation
- [ ] Error handling review (all stages)
- [ ] Logging: structured JSON + custom events
- [ ] Pre-roll buffer size tuning (default 1000ms)
- [ ] Voice quality A/B: carlfm-x_low vs shared
- [ ] Cleanup: remove debug prints, add type hints
- [ ] Update README with pipeline architecture diagram

---

## Dependency Graph

```
Phase 1 (Foundation)
  ├── 1.1 → 1.2 → 1.3 → 1.4
  └── 1.5 depends on 1.2, 1.3, 1.4

Phase 2 (VAD)
  ├── 2.1 → 2.2 → 2.3
  └── 2.4 depends on 1.3, 2.1

Phase 3 (STT)
  ├── 3.1 → 3.2
  └── 3.3 depends on 2.4, 3.2

Phase 4 (TTS)
  ├── 4.1 → 4.2 → 4.3
  └── 4.4 depends on 4.1, 4.3

Phase 5 (Pipeline)
  ├── 5.1 → 5.2 → 5.3
  └── 5.4 depends on 3.3, 4.4, 5.3

Phase 6 (Integration)
  ├── 6.1 → 6.2 → 6.3 → 6.4 → 6.5 → 6.6
  └── All depend on Phase 5 completion
```

---

## Estimated Effort

| Phase | Tasks | Est. Days | Key Risk |
|-------|-------|-----------|----------|
| 1 Foundation | 5 | 2 | Thread-safety in ring buffer |
| 2 VAD | 4 | 2 | Silero ONNX export |
| 3 STT | 3 | 2 | Streaming boundary handling |
| 4 TTS | 4 | 3 | Piper streaming + fallback |
| 5 Pipeline | 4 | 4 | State machine + barge-in |
| 6 Integration | 6 | 3 | Benchmark CI gate |

**Total: ~16 working days (~3.5 weeks)**

---

## Acceptance Criteria Mapping

| Spec Scenario | Test Task |
|---------------|-----------|
| 1. Basic turn < 800ms | 6.3 Benchmark + 6.4 Acceptance |
| 2. Barge-in < 300ms | 5.3 Barge-in + 6.3 Benchmark |
| 3. 10min stability | 6.3 Stability test |
| 4. VAD noise < 5% | 2.4 + 6.3 VAD robustness |
| 5. TTS fallback | 4.3 Fallback + 6.4 Acceptance |
| 6. Rapid interruptions | 5.3 Barge-in + 6.4 Acceptance |

---

## Open Questions (Resolved in Design)

| Question | Decision |
|----------|----------|
| Silero vs WebRTC | Silero ONNX primary, WebRTC fallback |
| Piper voice | es_ES-carlfm-x_low |
| Chunking | Sentence (.!?) + min 10 chars |
| Pre-roll | 1000ms |
| Barge-in threshold | Same as VAD (0.5) |
| Fallback mid-sentence | Continue with pyttsx3 |
| Config format | .env + YAML |
| Observability | JSON logs + events |
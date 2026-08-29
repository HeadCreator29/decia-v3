# Spec: Modern Voice Pipeline for DECIA v3

## ADDED Requirements

### Requirement: Voice Activity Detection (VAD) — Silero
The system SHALL provide real-time voice activity detection using Silero VAD (ONNX model).
- Input: 512-sample frames @ 16kHz (32ms frames)
- Output: Speech probability (0.0-1.0) per frame + `speech_start` / `speech_end` events
- Configurable threshold (default 0.5), minimum speech duration (default 250ms), minimum silence duration (default 100ms)
- MUST run in real-time callback (< 5ms per frame)
- MUST support ONNX runtime (no torch required at inference)

### Requirement: Streaming Speech-to-Text (STT)
The system SHALL provide streaming transcription using faster-whisper with `stream=True`.
- Input: Audio buffer from VAD-detected speech segments
- Output: Partial transcription callbacks (real-time) → Final transcription on segment end
- Language: Spanish (configurable)
- Model: small (configurable), CPU int8
- MUST emit partial results every ~500ms or on word boundaries
- MUST handle segment boundaries cleanly (no word splitting)

### Requirement: Streaming Text-to-Speech (TTS)
The system SHALL provide streaming speech synthesis using Piper TTS.
- Voice: `es_ES-carlfm-x_low` (configurable)
- Input: Text stream (sentence chunks from LLM)
- Output: Audio chunks (PCM 22.05kHz, 16-bit, mono) via callback
- First chunk latency < 100ms after first text chunk received
- Chunking strategy: Sentence-level (split on .!?), minimum 10 chars
- MUST support `stop()` for barge-in interruption
- MUST support voice configuration (speed, speaker_id if multi-speaker)

### Requirement: Barge-In / Interruption Handling
The system SHALL detect user speech during TTS playback and interrupt immediately.
- VAD monitoring active during SPEAKING state
- On `speech_start` during SPEAKING:
  - Stop AudioOutput immediately (< 50ms)
  - Flush all pipeline queues (STT, LLM, TTS)
  - Preserve pre-roll buffer (last 2s audio)
  - Transition to CAPTURING state
  - Resume from preserved buffer
- Barge-in detection latency < 300ms from user speech onset
- MUST NOT lose user utterance that triggered barge-in

### Requirement: Pipeline Orchestration & State Machine
The system SHALL orchestrate all components via asyncio state machine.
- States: `LISTENING` → `CAPTURING` → `PROCESSING` → `THINKING` → `SPEAKING`
- Transitions triggered by VAD events, pipeline completion, barge-in
- Queue-based communication between stages (asyncio.Queue, maxsize=10)
- Graceful shutdown: drain queues, stop audio streams, cancel tasks
- Error handling: stage failure → log → transition to LISTENING (or fallback)

### Requirement: Audio I/O & Ring Buffer
The system SHALL manage audio with sounddevice callback mode.
- Sample rate: 16kHz (VAD/STT), 22.05kHz (TTS output)
- Ring buffer: 2 seconds pre-roll (configurable)
- Callback mode (non-blocking) for both input and output
- Thread-safe queues between callback thread and asyncio event loop
- Sample format: float32 (-1.0 to 1.0) internally, int16 for DAC

### Requirement: Fallback Chain
The system SHALL provide graceful degradation.
- TTS fallback: Piper → pyttsx3 → silence (in order)
- On Piper failure: log error, switch to pyttsx3 for current utterance
- On pyttsx3 failure: silent skip, log error, continue pipeline
- STT fallback: Whisper built-in VAD if Silero fails
- VAD fallback: WebRTC VAD if Silero ONNX unavailable

### Requirement: Configuration
The system SHALL be configurable via environment variables and/or config file.
- VAD: threshold, min_speech_ms, min_silence_ms, pre_roll_ms
- STT: model_size, language, beam_size, compute_type
- TTS: voice_id, speed, chunk_strategy
- Audio: sample_rate, device_id, blocksize
- Pipeline: queue_sizes, timeouts, latency_budget_ms

---

## CHANGED Requirements (from current implementation)

### Requirement: Non-Blocking Main Loop
The main conversation loop SHALL NOT block on any single stage.
- REPLACE: Sequential `listen()` → `think()` → `speak()` blocking calls
- WITH: Pipeline.start() → event-driven callbacks → Pipeline.stop()
- Context management (ConversationContext) preserved

### Requirement: Latency Budget
End-to-end latency SHALL meet p95 < 800ms (mic → first audio out).
- Breakdown budget: VAD 50ms + STT 300ms + Intent 20ms + LLM 200ms + TTS 100ms + Audio 30ms = 700ms (100ms margin)
- CI gate: benchmark test must pass p95 < 800ms

---

## SCENARIOS

### Scenario 1: Basic Conversation Turn
**Given** DECIA is in LISTENING state
**When** User says "hola"
**Then** 
- VAD detects speech_start within 50ms
- STT streams partial "hola" → final "hola"
- Intent classifies GREETING
- LLM streams response tokens
- TTS generates first audio chunk within 100ms of first token
- Audio plays via AudioOutput
- Total latency < 800ms p95

### Scenario 2: Barge-In During Long Response
**Given** DECIA is SPEAKING "Hola, ¿cómo estás? Todo bien por aquí, y tú qué tal..."
**When** User says "para" at t=1.5s into DECIA's speech
**Then**
- VAD detects speech_start during SPEAKING state within 300ms
- AudioOutput.stop() called immediately
- TTSProcessor.stop() called, queues flushed
- Pipeline transitions to CAPTURING with pre-roll buffer
- User's "para" captured and processed as new turn
- No audio artifacts or lost speech

### Scenario 3: Continuous Conversation
**Given** Pipeline running for 10 minutes
**When** Multiple back-and-forth turns with varying lengths
**Then**
- No audio dropouts (buffer underruns)
- No memory leaks (stable RAM < 500MB)
- Latency stable (p95 < 800ms throughout)
- State machine transitions clean, no stuck states

### Scenario 4: Noise Robustness
**Given** Background noise (fan 40dB, TV 50dB at 3m)
**When** No user speech for 30 seconds
**Then**
- VAD false positive rate < 5% (measured over 10 min noise-only)
- No spurious CAPTURING transitions
- No false barge-in triggers during SPEAKING

### Scenario 5: TTS Fallback
**Given** Piper TTS fails mid-stream (model error, OOM, missing voice)
**When** TTSProcessor detects failure
**Then**
- Log error with context
- Switch to pyttsx3 for remainder of current utterance
- User hears seamless transition (no silence gap > 50ms)
- Pipeline continues, logs fallback event
- Next utterance attempts Piper again

### Scenario 6: Rapid Interruptions
**Given** DECIA starts speaking
**When** User interrupts 3 times in quick succession (< 1s between)
**Then**
- Each interruption handled cleanly
- No queue buildup or deadlock
- Last user utterance processed correctly
- Pipeline returns to LISTENING after last interruption

---

## ACCEPTANCE CRITERIA (Testable)

### Functional
- [ ] All 6 scenarios pass in integration test suite
- [ ] Barge-in works at any point in SPEAKING state
- [ ] Pre-roll buffer preserves interrupted utterance
- [ ] Fallback chain activates correctly on failures
- [ ] Configuration via env vars works end-to-end

### Performance
- [ ] p95 latency < 800ms (1000 samples, CI benchmark)
- [ ] Barge-in detection < 300ms (100 interruption tests)
- [ ] VAD false positive < 5% (10 min noise recording)
- [ ] Memory stable < 500MB over 10 min conversation
- [ ] CPU < 50% single core on RPi4-class hardware

### Regression
- [ ] All existing 354 tests pass unchanged
- [ ] IntentLayer classification accuracy unchanged
- [ ] Transcription corrections (speech_corrections) still apply
- [ ] Ollama streaming integration works (token-by-token)

---

## OPEN QUESTIONS (to resolve in Design)

1. **VAD**: Silero ONNX (needs torch for export) vs WebRTC VAD (pure Python, lighter)?
2. **Piper Voice**: `es_ES-carlfm-x_low` (fast, lower quality) vs `es_ES-shared` (better quality)?
3. **Chunking**: Sentence split (.!?) vs fixed N words vs semantic (comma-aware)?
4. **Pre-roll**: 500ms (low mem) vs 1s (balanced) vs 2s (max context)?
5. **Barge-in threshold**: Same as main VAD or separate sensitivity?
6. **Fallback behavior**: Piper failure mid-sentence → pyttsx3 continues same sentence or restarts?
7. **Config format**: .env only vs YAML config vs CLI args?
8. **Observability**: Structured logging vs Prometheus metrics vs custom events?

---

## DELIVERABLES FOR NEXT PHASES

1. **Design** (sdd-design):
   - API contracts (interfaces for each processor)
   - Data structures (queues, events, state)
   - Threading model (callback thread ↔ asyncio)
   - Error handling strategy per stage
   - Benchmark harness design

2. **Tasks** (sdd-tasks):
   - Phase 1: Foundation (VAD, ring buffer, tests)
   - Phase 2: Streaming STT
   - Phase 3: Streaming TTS + Piper integration
   - Phase 4: Pipeline orchestration + state machine
   - Phase 5: Barge-in + interruption handling
   - Phase 6: Integration + benchmarks + polish

3. **Implementation** (sdd-apply): 6 phases over ~4 weeks

4. **Verification** (sdd-verify): Acceptance tests + CI benchmarks

5. **Archive** (sdd-archive): Delta spec sync
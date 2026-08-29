# Proposal: Modern Voice Pipeline for DECIA v3

## Problem Statement

Current DECIA voice loop is sequential and blocking:
```python
while True:
    raw = listen()      # Blocking STT (Whisper + 1.2s silence)
    response = think()  # Blocking LLM
    speak(response)     # Blocking TTS (pyttsx3 runAndWait)
```

**Problems:**
- No interruption capability (user can't stop DECIA mid-sentence)
- No streaming (full STT → full LLM → full TTS before any audio)
- High latency: ~2-3 seconds end-to-end
- Poor UX: feels like a voice recorder, not a conversational agent

## Scope

### In Scope
- Voice Activity Detection (VAD) with Silero
- Streaming STT with faster-whisper (`stream=True`)
- Streaming TTS with Piper (`es_ES-carlfm-x_low`)
- Barge-in / interruption handling
- Pipeline orchestration with asyncio state machine

### Out of Scope
- Wake word / keyword spotting
- Speaker diarization / multi-user
- Voice cloning / custom voices
- Cloud TTS (OpenAI, ElevenLabs, etc.)
- Audio effects / noise suppression (optional later)

## Success Criteria (Measurable)

| Metric | Target |
|--------|--------|
| End-to-end latency (p95) | < 800ms (mic → first audio out) |
| Barge-in detection | < 300ms after user starts speaking |
| VAD false positive rate | < 5% in typical home noise |
| Regression on existing tests | 0 (all 354 tests pass) |
| Streaming TTS first chunk | < 100ms after first LLM token |

## Acceptance Tests

1. **Basic response**: User says "hola" → DECIA responds with audio within 800ms
2. **Barge-in**: DECIA speaking "hola como estas..." → user says "para" at 1.5s → DECIA stops within 300ms
3. **Long conversation**: 10 min continuous conversation → no audio dropouts, no memory leaks
4. **Noise robustness**: Background fan/TV → VAD false positive < 5%
5. **Fallback**: Piper fails mid-stream → seamless fallback to pyttsx3
6. **Rapid interruptions**: User interrupts 3 times quickly (< 1s between) → no deadlock

## Architecture Decisions

| Layer | Choice | Rationale |
|-------|--------|-----------|
| **VAD** | Silero ONNX primary, WebRTC fallback | Best accuracy/latency, streaming, MIT |
| **STT** | faster-whisper streaming (`stream=True`) | Already integrated, add `stream=True` |
| **TTS** | Piper `es_ES-carlfm-x_low` | Fastest streaming, offline, MIT |
| **Audio I/O** | sounddevice callback mode | Already in use, async native |
| **Fallback TTS** | pyttsx3 | Zero-dep, already works |
| **Orchestration** | asyncio + custom state machine | No heavy framework, full control |

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Streaming complexity bugs | High | High | Comprehensive state machine tests, property-based testing |
| Thread safety audio callbacks | Medium | High | Thread-safe queues, no locks in callbacks |
| Latency regression | Medium | High | CI benchmark gate (< 800ms p95) |
| Silero VAD false positives | Medium | High | Tunable threshold, noise gate, min speech duration |
| Piper voice quality | Low | Medium | Keep pyttsx3 fallback, A/B test voices |
| Dependency bloat (torch) | Medium | Medium | ONNX export for Silero, WebRTC VAD fallback |

## Open Questions (to resolve in Spec/Design)

1. **VAD**: Silero (torch) vs WebRTC VAD (lighter, less accurate)?
2. **Piper Voice**: `es_ES-carlfm-x_low` vs `es_ES-shared`?
3. **Chunking**: Sentence-level (.!?) vs fixed N words vs semantic?
4. **Pre-roll**: 500ms? 1s? 2s?
5. **Barge-in threshold**: Same as main VAD or separate sensitivity?
6. **Fallback chain**: Piper → pyttsx3 → silence? Mid-sentence behavior?
7. **Metrics/Observability**: Structured logs vs Prometheus vs custom events?
8. **Config Surface**: .env only vs YAML config vs CLI args?

## Delivery Strategy

- **Execution mode**: auto (automatic phases)
- **Artifact store**: hybrid (Engram + OpenSpec)
- **PR strategy**: auto-chain with feature-branch-chain
- **Review budget**: 800 lines
- **Chain strategy**: feature-branch-chain (each PR targets previous PR branch)

## Deliverables

1. ✅ Exploration (completed)
2. ✅ Proposal (this document)
3. ⏳ Spec (delta requirements + scenarios)
4. ⏳ Design (technical architecture + API contracts)
5. ⏳ Tasks (implementation breakdown by phase)
6. ⏳ Implementation (6 phases over ~4 weeks)
6. ⏳ Verification (acceptance tests + CI benchmarks)
7. ⏳ Archive (delta spec sync)

---

**Status**: Ready for Spec phase
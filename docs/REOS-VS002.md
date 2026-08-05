# REOS Vertical Slice 002 — Multi-Basin Constitutional Decision Pipeline

## Status

FROZEN

## Purpose

REOS-VS002 proves that one governed Recognition Unit can move through a deterministic multi-basin decision pipeline while preserving strict ownership, lineage, telemetry, reproducibility, and fail-closed execution.

## Constitutional Pipeline

```text
GovernedIngressPayload
        ↓
RecognitionUnit
        ↓
CandidateGenerationResult
        ↓
CandidateBasinEvaluation
        ↓
BasinSelection
        ↓
RecognitionResult
        +
TransitionTelemetry
```
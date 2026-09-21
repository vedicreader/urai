# Release notes

<!-- do not remove -->

## 0.0.7
`stream_resp` assembles one reply from a `StreamSplit`, so every backend shares a drain loop. `StreamSplit._held` no longer rescans every tag per chunk.
`CachedChat` covers `structured` and `runtime`, and takes the `env` its recording switch reads, so a host needs no recorder of its own.
`split_think` takes the closing tag a template prefill leaves with no opener; the text before it is thought.

## 0.0.6
tool rows for easy access

## 0.0.5
tag parsing fixes for mlx models. adding usage stats to record

## 0.0.4
uraiyadal release

## 0.0.3
rename to uraiyadal

## 0.0.2
release

## 0.0.1
initial urai creation

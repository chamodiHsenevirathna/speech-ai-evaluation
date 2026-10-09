#!/usr/bin/env bash
# Generates the M5 evaluation sample set.
#
# IMPORTANT / LIMITATION: this sandboxed development environment has no microphone
# access, so these are NOT real human recordings. They are synthesized locally via
# macOS `say` (text-to-speech) and converted to the same WebM/Opus container the
# browser produces, purely to exercise the real decode+transcribe pipeline end-to-end
# and to get a reference transcript we can trust exactly (since we wrote the script).
# They cannot substitute for real accented human speech - see conclusions.md for what
# this experiment can and cannot tell us, and README.md's manual-testing checklist for
# validating with real recordings.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p samples references

generate() {
  local name="$1"
  local voice="$2"
  local text="$3"
  echo "Generating $name..."
  say -v "$voice" -o "samples/${name}.aiff" "$text"
  ffmpeg -y -loglevel error -i "samples/${name}.aiff" -c:a libopus -b:a 32k "samples/${name}.webm"
  rm "samples/${name}.aiff"
  printf '%s' "$text" > "references/${name}.txt"
}

generate "clear_speech" "Samantha" \
  "The weather today is sunny with a light breeze, and I think it's a perfect afternoon for a walk in the park."

generate "natural_fillers" "Samantha" \
  "So, um, I think the the best way to explain this is, uh, well, it's kind of complicated but let me try."

generate "hesitation_restart" "Samantha" \
  "I wanted to talk about, I wanted to talk about my favorite hobby, which is, actually, let me start over, my favorite hobby is painting."

generate "conversational_pace" "Samantha" \
  "Last year I had to make a decision quickly when my flight got cancelled. I only had a few minutes to decide whether to rebook or take a bus instead, so I just went with my gut and booked the next available flight. It worked out fine in the end, but it was definitely a stressful moment."

# Near-silent sample: tests the "no speech detected" path, not TTS-generated.
echo "Generating near_silent..."
ffmpeg -y -loglevel error -f lavfi -i anullsrc=r=16000:cl=mono -t 3 -c:a libopus -b:a 32k samples/near_silent.webm
printf '%s' "" > references/near_silent.txt

echo "Done. Samples in samples/, reference transcripts in references/."
ls -la samples/

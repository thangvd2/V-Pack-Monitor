/**
 * Notification sounds using Web Audio API.
 * No external audio files needed — all sounds are synthesized.
 */

let audioCtx = null;

const _lastPlayed = {};
const COOLDOWN_MS = 600;

function _shouldPlay(soundType) {
  const now = Date.now();
  if (now - (_lastPlayed[soundType] || 0) < COOLDOWN_MS) return false;
  _lastPlayed[soundType] = now;
  return true;
}

async function getAudioContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  // Resume if suspended (browser autoplay policy)
  if (audioCtx.state === 'suspended') {
    await audioCtx.resume();
  }
  return audioCtx;
}

/**
 * Short ascending beep: 440Hz → 880Hz over 150ms.
 * Played when barcode is scanned and recording STARTS.
 */
export async function playScanStart() {
  if (!_shouldPlay('scan-start')) return;
  try {
    const ctx = await getAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(440, ctx.currentTime);
    osc.frequency.linearRampToValueAtTime(880, ctx.currentTime + 0.15);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
    osc.onended = () => {
      gain.disconnect();
      osc.disconnect();
    };
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.2);
  } catch (err) {
    console.warn('[notificationSounds]', err.message);
  }
}

/**
 * Short descending beep: 880Hz → 440Hz over 150ms.
 * Played when recording STOPS (STOP scanned or auto-stopped).
 */
export async function playRecordingStop() {
  if (!_shouldPlay('recording-stop')) return;
  try {
    const ctx = await getAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.linearRampToValueAtTime(440, ctx.currentTime + 0.15);
    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
    osc.onended = () => {
      gain.disconnect();
      osc.disconnect();
    };
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.2);
  } catch (err) {
    console.warn('[notificationSounds]', err.message);
  }
}

/**
 * Pleasant two-tone chime: 523Hz (C5) then 784Hz (G5).
 * Played when video processing is COMPLETE (READY status).
 */
export async function playVideoReady() {
  if (!_shouldPlay('video-ready')) return;
  try {
    const ctx = await getAudioContext();

    // First note: C5 (523Hz)
    const osc1 = ctx.createOscillator();
    const gain1 = ctx.createGain();
    osc1.type = 'sine';
    osc1.connect(gain1);
    gain1.connect(ctx.destination);
    osc1.frequency.setValueAtTime(523, ctx.currentTime);
    gain1.gain.setValueAtTime(0.3, ctx.currentTime);
    gain1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.2);
    osc1.onended = () => {
      gain1.disconnect();
      osc1.disconnect();
    };
    osc1.start(ctx.currentTime);
    osc1.stop(ctx.currentTime + 0.2);

    // Second note: G5 (784Hz) — starts 150ms after first
    const osc2 = ctx.createOscillator();
    const gain2 = ctx.createGain();
    osc2.type = 'sine';
    osc2.connect(gain2);
    gain2.connect(ctx.destination);
    osc2.frequency.setValueAtTime(784, ctx.currentTime + 0.15);
    gain2.gain.setValueAtTime(0.3, ctx.currentTime + 0.15);
    gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.35);
    osc2.onended = () => {
      gain2.disconnect();
      osc2.disconnect();
    };
    osc2.start(ctx.currentTime + 0.15);
    osc2.stop(ctx.currentTime + 0.35);
  } catch (err) {
    console.warn('[notificationSounds]', err.message);
  }
}

// Warm up AudioContext on first user gesture so resume() is a no-op later
function _initOnGesture() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') audioCtx.resume();
  document.removeEventListener('click', _initOnGesture);
  document.removeEventListener('keydown', _initOnGesture);
}
document.addEventListener('click', _initOnGesture);
document.addEventListener('keydown', _initOnGesture);

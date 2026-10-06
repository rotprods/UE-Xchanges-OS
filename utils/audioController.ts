class AudioController {
  private ctx: AudioContext | null = null;
  private ambientOsc: OscillatorNode | null = null;
  private ambientGain: GainNode | null = null;
  private isEnabled: boolean = false;

  constructor() {
    // AudioContext will be initialized on first user interaction
  }

  public init() {
    if (this.ctx) return;
    try {
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      this.ctx = new AudioCtx();
    } catch (e) {
      console.warn("Web Audio API is not supported in this browser", e);
    }
  }

  public enable() {
    this.init();
    if (!this.ctx) return;

    if (this.ctx.state === "suspended") {
      this.ctx.resume();
    }

    this.isEnabled = true;
    this.startAmbientHum();
  }

  public disable() {
    this.isEnabled = false;
    this.stopAmbientHum();
  }

  public toggle() {
    if (this.isEnabled) {
      this.disable();
    } else {
      this.enable();
    }
    return this.isEnabled;
  }

  public getStatus() {
    return this.isEnabled;
  }

  private startAmbientHum() {
    if (!this.ctx || !this.isEnabled) return;
    try {
      this.stopAmbientHum();

      // Create low frequency hum (sub-bass carrier)
      this.ambientOsc = this.ctx.createOscillator();
      this.ambientGain = this.ctx.createGain();

      this.ambientOsc.type = "sine";
      this.ambientOsc.frequency.setValueAtTime(55, this.ctx.currentTime); // A1 note, deep hum

      this.ambientGain.gain.setValueAtTime(0.0, this.ctx.currentTime);
      // Fade in smoothly
      this.ambientGain.gain.linearRampToValueAtTime(0.08, this.ctx.currentTime + 2.0);

      this.ambientOsc.connect(this.ambientGain);
      this.ambientGain.connect(this.ctx.destination);

      this.ambientOsc.start();
    } catch (e) {
      console.error("Failed to start ambient hum", e);
    }
  }

  private stopAmbientHum() {
    try {
      if (this.ambientOsc) {
        this.ambientOsc.stop();
        this.ambientOsc.disconnect();
        this.ambientOsc = null;
      }
      if (this.ambientGain) {
        this.ambientGain.disconnect();
        this.ambientGain = null;
      }
    } catch (e) {
      // already stopped
    }
  }

  // Plays a robotic cyber tick
  public playTick(frequency: number = 800, duration: number = 0.05, gainValue: number = 0.03) {
    if (!this.ctx || !this.isEnabled) return;
    try {
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = "triangle";
      osc.frequency.setValueAtTime(frequency, this.ctx.currentTime);
      // pitch bend downwards for a clicky sound
      osc.frequency.exponentialRampToValueAtTime(100, this.ctx.currentTime + duration);

      gain.gain.setValueAtTime(gainValue, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      // ignore errors in background audio
    }
  }

  // Plays a digital error/warning chime
  public playWarning() {
    if (!this.ctx || !this.isEnabled) return;
    try {
      const now = this.ctx.currentTime;
      
      // Note 1
      const osc1 = this.ctx.createOscillator();
      const gain1 = this.ctx.createGain();
      osc1.type = "sawtooth";
      osc1.frequency.setValueAtTime(150, now);
      gain1.gain.setValueAtTime(0.05, now);
      gain1.gain.exponentialRampToValueAtTime(0.0001, now + 0.15);
      osc1.connect(gain1);
      gain1.connect(this.ctx.destination);
      osc1.start();
      osc1.stop(now + 0.15);

      // Note 2 slightly offset
      setTimeout(() => {
        if (!this.ctx || !this.isEnabled) return;
        const osc2 = this.ctx.createOscillator();
        const gain2 = this.ctx.createGain();
        osc2.type = "sawtooth";
        osc2.frequency.setValueAtTime(120, this.ctx.currentTime);
        gain2.gain.setValueAtTime(0.05, this.ctx.currentTime);
        gain2.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.2);
        osc2.connect(gain2);
        gain2.connect(this.ctx.destination);
        osc2.start();
        osc2.stop(this.ctx.currentTime + 0.2);
      }, 80);
    } catch (e) {
      // ignore
    }
  }

  // Plays a deep submarine sonar ping for massive Whale Alerts
  public playWhaleSonarPing() {
    if (!this.ctx || !this.isEnabled) return;
    try {
      const now = this.ctx.currentTime;
      const duration = 2.0;

      // Ping oscillator (Sine wave)
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(800, now);
      osc.frequency.exponentialRampToValueAtTime(400, now + duration);

      // Attack and release for the ping
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.15, now + 0.05); // quick attack
      gain.gain.exponentialRampToValueAtTime(0.0001, now + duration); // long fade

      // Reverb/echo effect (delay)
      const delay = this.ctx.createDelay();
      delay.delayTime.value = 0.4;
      const feedback = this.ctx.createGain();
      feedback.gain.value = 0.3;
      
      osc.connect(gain);
      gain.connect(this.ctx.destination);
      gain.connect(delay);
      delay.connect(feedback);
      feedback.connect(delay);
      delay.connect(this.ctx.destination);

      osc.start(now);
      osc.stop(now + duration);
    } catch (e) {
      // ignore
    }
  }
}

// Export a single instance
export const audioController = new AudioController();

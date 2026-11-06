(function () {
  "use strict";

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synth = window.speechSynthesis;
  let recognition = null;
  let listening = false;
  let continuous = false;
  let voiceEnabled = true;
  let finalizedText = "";
  let interimText = "";
  let lastSubmitted = "";
  let lastSubmittedAt = 0;

  function getCookie(name) {
    const value = "; " + document.cookie;
    const parts = value.split("; " + name + "=");
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(";").shift());
    return "";
  }

  function speak(text) {
    if (!voiceEnabled || !synth) return;
    try { synth.cancel(); const u = new SpeechSynthesisUtterance(text); u.rate = 1; u.lang = "en-IN"; synth.speak(u); } catch (e) {}
  }

  function setStatus(panel, text, state) {
    const status = panel.querySelector(".voice-status");
    if (status) { status.textContent = text; status.dataset.state = state || "idle"; }
  }
  function setInputValue(panel, value) {
    const input = panel.querySelector(".voice-text-form input");
    if (input) {
      input.value = value;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }
  }
  function getInputValue(panel) {
    const input = panel.querySelector(".voice-text-form input");
    return input ? input.value : "";
  }
  function setRecognized(panel, text) {
    const el = panel.querySelector(".voice-recognized");
    if (el) el.textContent = text || "";
  }
  function setResponse(panel, text) {
    const el = panel.querySelector(".voice-response");
    if (el) el.textContent = text || "";
  }
  function addMessage(panel, role, text) {
    const log = panel.querySelector(".voice-log");
    if (!log) return;
    const div = document.createElement("div");
    div.className = "voice-msg voice-msg-" + role;
    const time = new Date().toLocaleTimeString();
    div.innerHTML = "<strong>" + role + "</strong> <small>" + time + "</small><div>" + text + "</div>";
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }

  async function submitVoiceCommand(transcript, panel) {
    const text = (transcript || "").trim();
    if (!text) { setResponse(panel, "Please enter a command."); return; }
    const now = Date.now();
    if (text === lastSubmitted && now - lastSubmittedAt < 1500) return;
    lastSubmitted = text;
    lastSubmittedAt = now;
    setResponse(panel, "");
    setStatus(panel, "Sending command...", "processing");
    console.log("Voice command submitted:", text);
    const csrftoken = getCookie("csrftoken");
    try {
      const response = await fetch("/healthcare/voice-command/", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrftoken },
        body: JSON.stringify({ transcript: text }),
      });
      if (response.status === 401 || response.status === 403) {
        const msg = "Please log in to use voice navigation.";
        setResponse(panel, msg); speak(msg); addMessage(panel, "assistant", msg);
        setStatus(panel, "Ready", "idle");
        return;
      }
      const data = await response.json();
      console.log("Backend response:", data);
      setResponse(panel, data.message || "");
      speak(data.message || "");
      addMessage(panel, "assistant", data.message || "");
      if (data.action === "navigate" && data.url) {
        setStatus(panel, "Navigating...", "executing");
        window.location.href = data.url;
      } else if (data.action === "back") {
        window.history.back();
      } else if (data.action === "scroll_down") {
        window.scrollBy({ top: window.innerHeight * 0.8, behavior: "smooth" });
      } else if (data.action === "scroll_up") {
        window.scrollBy({ top: -window.innerHeight * 0.8, behavior: "smooth" });
      } else if (data.action === "refresh") {
        window.location.reload();
      } else if (data.action === "stop") {
        stopListening(panel);
      } else {
        setStatus(panel, "Ready", "idle");
      }
    } catch (e) {
      console.error("Voice command error:", e);
      const msg = "Voice command could not be processed. Please try again.";
      setResponse(panel, msg); speak(msg); addMessage(panel, "assistant", msg);
      setStatus(panel, "Error", "error");
    }
  }

  function stopListening(panel) {
    listening = false;
    continuous = false;
    if (recognition) {
      try { recognition.stop(); } catch (e) {}
    }
    interimText = "";
    setStatus(panel, "Stopped listening.", "idle");
    console.log("Recognition stopped");
  }

  function startListening(panel) {
    if (!SpeechRecognition) {
      const msg = "Voice recognition is not supported in this browser. Use the text command box instead.";
      setResponse(panel, msg); speak(msg); addMessage(panel, "assistant", msg);
      return;
    }
    if (listening) { stopListening(panel); return; }
    // New session: clear transcript
    finalizedText = "";
    interimText = "";
    setInputValue(panel, "");
    setRecognized(panel, "");
    setStatus(panel, "Requesting microphone permission...", "processing");
    console.log("Requesting microphone permission");
    recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.continuous = true;

    recognition.onstart = function () {
      listening = true;
      setStatus(panel, "Listening...", "listening");
      console.log("Speech recognition started");
      const input = panel.querySelector(".voice-text-form input");
      if (input) input.focus();
    };

    recognition.onresult = function (event) {
      let newFinal = "";
      let newInterim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          newFinal += t;
        } else {
          newInterim += t;
        }
      }
      if (newFinal) {
        finalizedText = (finalizedText + " " + newFinal).trim();
        console.log("Final transcript received:", newFinal);
      }
      interimText = newInterim.trim();
      const combined = (finalizedText + (interimText ? " " + interimText : "")).trim();
      console.log("Text input updated:", combined);
      setInputValue(panel, combined);
      setRecognized(panel, combined);
      if (combined) setStatus(panel, "Speech captured / listening...", "listening");
    };

    recognition.onerror = function (event) {
      listening = false;
      let msg = "Voice recognition could not start. Please try again.";
      switch (event.error) {
        case "not-allowed": msg = "Microphone access is blocked. Please allow microphone access in browser settings."; break;
        case "service-not-allowed": msg = "Speech service is not allowed. Check browser settings."; break;
        case "no-speech": msg = "No speech detected. Please try again."; break;
        case "audio-capture": msg = "No microphone found. Connect a microphone and retry."; break;
        case "network": msg = "Network error during speech recognition. Check your connection."; break;
        case "aborted": msg = "Speech recognition was aborted."; break;
      }
      console.error("Speech recognition error:", event.error);
      setStatus(panel, "Voice error", "error");
      setResponse(panel, msg); speak(msg); addMessage(panel, "assistant", msg);
    };

    recognition.onend = function () {
      console.log("Recognition ended");
      if (continuous && listening) {
        try { recognition.start(); } catch (e) { listening = false; setStatus(panel, "Voice assistant stopped.", "idle"); }
      } else {
        listening = false;
        // keep text in input
        const combined = (finalizedText + (interimText ? " " + interimText : "")).trim();
        setInputValue(panel, combined);
        setStatus(panel, "Speech captured. Ready to send.", "idle");
      }
    };

    try {
      recognition.start();
      console.log("Microphone permission requested");
    } catch (e) {
      console.error("Failed to start recognition:", e);
      listening = false;
      const msg = "Voice recognition could not start. Please try again.";
      setStatus(panel, "Voice error", "error");
      setResponse(panel, msg); speak(msg);
    }
  }

  function buildPanel() {
    const btn = document.createElement("button");
    btn.className = "voice-fab";
    btn.setAttribute("aria-label", "Open voice assistant");
    btn.innerHTML = "🎤";
    document.body.appendChild(btn);

    const panel = document.createElement("section");
    panel.className = "voice-panel";
    panel.setAttribute("aria-label", "Voice assistant");
    panel.innerHTML = `
      <div class="voice-header">
        <div><strong>Healthcare AI Assistant</strong><br><small class="voice-status" data-state="idle">Ready</small></div>
        <div>
          <button type="button" class="voice-minimize">—</button>
          <button type="button" class="voice-close">✕</button>
        </div>
      </div>
      <div class="voice-body">
        <div class="voice-log"></div>
        <p><strong>Heard:</strong> <span class="voice-recognized"></span></p>
        <p><strong>Response:</strong> <span class="voice-response"></span></p>
        <div class="voice-controls">
          <button type="button" class="btn voice-start">🎤 Start Listening</button>
          <button type="button" class="btn btn-danger voice-stop">Stop</button>
          <button type="button" class="btn btn-secondary voice-clear">Clear Text</button>
          <label><input type="checkbox" class="voice-continuous"> Continuous</label>
          <label><input type="checkbox" class="voice-tts" checked> Voice responses</label>
        </div>
        <form class="voice-text-form">
          <input type="text" placeholder="Type or speak a command">
          <button type="submit" class="btn btn-secondary">Send</button>
        </form>
        <details>
          <summary>Suggested commands</summary>
          <ul>
            <li>Open dashboard</li>
            <li>Find a doctor</li>
            <li>Show my appointments</li>
            <li>Open prescriptions</li>
            <li>Show my medical records</li>
            <li>Open lab reports</li>
            <li>Show notifications</li>
            <li>Start symptom assessment</li>
            <li>Open healthcare chatbot</li>
            <li>Help</li>
          </ul>
        </details>
      </div>
    `;
    document.body.appendChild(panel);

    const body = panel.querySelector(".voice-body");
    btn.addEventListener("click", function () {
      panel.classList.toggle("open");
      if (panel.classList.contains("open")) {
        addMessage(panel, "assistant", "Hello! Speak or type a command. Try: Find a doctor.");
        speak("Hello! Speak or type a command.");
      }
    });
    panel.querySelector(".voice-close").addEventListener("click", function () { panel.classList.remove("open"); stopListening(panel); if (synth) synth.cancel(); });
    panel.querySelector(".voice-minimize").addEventListener("click", function () { body.hidden = !body.hidden; });

    const startButton = panel.querySelector(".voice-start");
    const stopButton = panel.querySelector(".voice-stop");
    const clearButton = panel.querySelector(".voice-clear");
    const continuousCheckbox = panel.querySelector(".voice-continuous");
    const ttsCheckbox = panel.querySelector(".voice-tts");
    const textForm = panel.querySelector(".voice-text-form");
    const textInput = textForm.querySelector("input");

    ttsCheckbox.addEventListener("change", function () { voiceEnabled = ttsCheckbox.checked; });
    clearButton.addEventListener("click", function () {
      finalizedText = ""; interimText = "";
      setInputValue(panel, "");
      setRecognized(panel, "");
      setStatus(panel, "Text cleared.", "idle");
    });

    startButton.addEventListener("click", function () {
      continuous = continuousCheckbox.checked;
      startListening(panel);
    });
    stopButton.addEventListener("click", function () { stopListening(panel); });
    continuousCheckbox.addEventListener("change", function () { continuous = continuousCheckbox.checked; });

    textForm.addEventListener("submit", function (e) {
      e.preventDefault();
      const transcript = getInputValue(panel).trim();
      if (transcript) {
        addMessage(panel, "user", transcript);
        submitVoiceCommand(transcript, panel);
      }
    });

    if (!SpeechRecognition) {
      startButton.disabled = true;
      setStatus(panel, "Voice recognition not supported. Use text commands.", "error");
    }
    if (!window.isSecureContext) {
      setStatus(panel, "Microphone requires HTTPS or localhost.", "error");
    }
    return panel;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildPanel);
  } else {
    buildPanel();
  }
})();
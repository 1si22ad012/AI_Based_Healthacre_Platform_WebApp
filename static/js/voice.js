(function () {
  "use strict";

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synth = window.speechSynthesis;
  let recognition = null;
  let listening = false;
  let continuous = false;

  function getCookie(name) {
    const value = "; " + document.cookie;
    const parts = value.split("; " + name + "=");
    if (parts.length === 2) {
      return decodeURIComponent(parts.pop().split(";").shift());
    }
    return "";
  }

  function speak(text) {
    if (!synth) return;
    try {
      synth.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1;
      utterance.lang = "en-IN";
      synth.speak(utterance);
    } catch (error) {
      // Text-to-speech is an enhancement only.
    }
  }

  function setStatus(panel, text, state) {
    const status = panel.querySelector(".voice-status");
    if (status) {
      status.textContent = text;
      status.dataset.state = state || "idle";
    }
  }

  function setRecognized(panel, text) {
    const recognized = panel.querySelector(".voice-recognized");
    if (recognized) recognized.textContent = text || "";
  }

  function setResponse(panel, text) {
    const response = panel.querySelector(".voice-response");
    if (response) response.textContent = text || "";
  }

  async function sendCommand(transcript, panel) {
    const csrftoken = getCookie("csrftoken");
    try {
      const response = await fetch("/healthcare/voice-command/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ transcript: transcript }),
      });
      if (response.status === 401 || response.status === 403) {
        const message = "Please log in to use voice navigation.";
        setResponse(panel, message);
        speak(message);
        return;
      }
      const data = await response.json();
      setResponse(panel, data.message || "");
      speak(data.message || "");
      if (data.action === "navigate" && data.url) {
        window.location.href = data.url;
      } else if (data.action === "back") {
        window.history.back();
      } else if (data.action === "scroll_down") {
        window.scrollBy({ top: window.innerHeight * 0.8, behavior: "smooth" });
      } else if (data.action === "scroll_up") {
        window.scrollBy({ top: -window.innerHeight * 0.8, behavior: "smooth" });
      } else if (data.action === "stop") {
        stopListening(panel);
      }
    } catch (error) {
      const message = "Voice command could not be processed. Please try again.";
      setResponse(panel, message);
      speak(message);
    }
  }

  function stopListening(panel) {
    listening = false;
    continuous = false;
    if (recognition) {
      try {
        recognition.stop();
      } catch (error) {
        // Recognition may already be stopped.
      }
    }
    setStatus(panel, "Voice assistant stopped.", "idle");
  }

  function startListening(panel) {
    if (!SpeechRecognition) {
      const message = "Voice recognition is not supported in this browser. Use the text command box instead.";
      setResponse(panel, message);
      speak(message);
      return;
    }
    if (listening) {
      stopListening(panel);
      return;
    }
    if (!recognition) {
      recognition = new SpeechRecognition();
      recognition.lang = "en-IN";
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      recognition.onstart = function () {
        listening = true;
        setStatus(panel, "Listening...", "listening");
      };
      recognition.onresult = function (event) {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          transcript += event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            setRecognized(panel, transcript.trim());
            sendCommand(transcript.trim(), panel);
            if (!continuous) {
              stopListening(panel);
            }
          } else {
            setRecognized(panel, transcript.trim());
          }
        }
      };
      recognition.onerror = function (event) {
        listening = false;
        const message = event.error === "not-allowed"
          ? "Microphone access is blocked. Please allow microphone access in your browser."
          : "Voice recognition could not start. Please try again.";
        setStatus(panel, "Voice error", "error");
        setResponse(panel, message);
        speak(message);
      };
      recognition.onend = function () {
        if (continuous && listening) {
          try {
            recognition.start();
          } catch (error) {
            listening = false;
            setStatus(panel, "Voice assistant stopped.", "idle");
          }
        } else {
          listening = false;
          setStatus(panel, "Voice assistant ready.", "idle");
        }
      };
    }
    setRecognized(panel, "");
    setResponse(panel, "");
    setStatus(panel, "Starting microphone...", "processing");
    try {
      recognition.start();
    } catch (error) {
      listening = false;
      const message = "Voice recognition could not start. Please try again.";
      setStatus(panel, "Voice error", "error");
      setResponse(panel, message);
      speak(message);
    }
  }

  function buildPanel() {
    const panel = document.createElement("section");
    panel.className = "voice-panel";
    panel.setAttribute("aria-label", "Voice assistant");
    panel.innerHTML = `
      <button type="button" class="voice-toggle btn btn-secondary" aria-expanded="false">Voice Assistant</button>
      <div class="voice-body" hidden>
        <p class="voice-status" data-state="idle">Voice assistant ready.</p>
        <p><strong>Heard:</strong> <span class="voice-recognized"></span></p>
        <p><strong>Response:</strong> <span class="voice-response"></span></p>
        <div class="voice-controls">
          <button type="button" class="btn voice-start">Start Listening</button>
          <button type="button" class="btn btn-danger voice-stop">Stop Listening</button>
          <label><input type="checkbox" class="voice-continuous"> Continuous listening</label>
        </div>
        <form class="voice-text-form">
          <label for="voice-text-input">Text command</label>
          <input id="voice-text-input" type="text" placeholder="Type a command">
          <button type="submit" class="btn btn-secondary">Send</button>
        </form>
        <details>
          <summary>Example commands</summary>
          <ul>
            <li>Open dashboard</li>
            <li>Show my appointments</li>
            <li>Open prescriptions</li>
            <li>Show my medical records</li>
            <li>Open lab reports</li>
            <li>Show notifications</li>
            <li>Find a doctor</li>
            <li>Start symptom assessment</li>
            <li>Open healthcare chatbot</li>
            <li>Help</li>
          </ul>
        </details>
      </div>
    `;
    document.body.appendChild(panel);

    const toggle = panel.querySelector(".voice-toggle");
    const body = panel.querySelector(".voice-body");
    const startButton = panel.querySelector(".voice-start");
    const stopButton = panel.querySelector(".voice-stop");
    const continuousCheckbox = panel.querySelector(".voice-continuous");
    const textForm = panel.querySelector(".voice-text-form");
    const textInput = panel.querySelector("#voice-text-input");

    toggle.addEventListener("click", function () {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", expanded ? "false" : "true");
      body.hidden = expanded;
      if (!expanded) {
        speak("Voice assistant opened.");
      }
    });

    startButton.addEventListener("click", function () {
      continuous = continuousCheckbox.checked;
      startListening(panel);
    });

    stopButton.addEventListener("click", function () {
      stopListening(panel);
    });

    continuousCheckbox.addEventListener("change", function () {
      continuous = continuousCheckbox.checked;
    });

    textForm.addEventListener("submit", function (event) {
      event.preventDefault();
      const transcript = textInput.value.trim();
      if (transcript) {
        setRecognized(panel, transcript);
        sendCommand(transcript, panel);
        textInput.value = "";
      }
    });

    if (!SpeechRecognition) {
      startButton.disabled = true;
      setStatus(panel, "Voice recognition is not supported in this browser. Use text commands.", "error");
    }

    return panel;
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", buildPanel);
  } else {
    buildPanel();
  }
})();

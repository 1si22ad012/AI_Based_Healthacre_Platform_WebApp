(function () {
  "use strict";
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const synth = window.speechSynthesis;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "btn btn-secondary";
  button.style.position = "fixed";
  button.style.bottom = "20px";
  button.style.left = "20px";
  button.textContent = "Voice Assistant";
  button.setAttribute("aria-label", "Start voice assistant");
  document.body.appendChild(button);

  function speak(text) {
    if (!synth) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1;
    synth.speak(utterance);
  }

  if (!SpeechRecognition) {
    button.disabled = true;
    button.textContent = "Voice unavailable";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "en-US";
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  recognition.onresult = function (event) {
    const command = event.results[0][0].transcript.toLowerCase();
    if (command.includes("appointment")) {
      window.location.href = "/appointments/";
      speak("Opening appointments.");
    } else if (command.includes("prescription")) {
      window.location.href = "/prescriptions/";
      speak("Opening prescriptions.");
    } else if (command.includes("notification")) {
      window.location.href = "/notifications/";
      speak("Opening notifications.");
    } else if (command.includes("dashboard")) {
      window.location.href = "/";
      speak("Opening dashboard.");
    } else {
      speak("I did not recognize that command. Try appointments, prescriptions, notifications, or dashboard.");
    }
  };

  recognition.onerror = function () {
    speak("Voice recognition is unavailable or permission was denied.");
  };

  button.addEventListener("click", function () {
    try {
      recognition.start();
      speak("Listening.");
    } catch (error) {
      speak("Voice recognition could not start.");
    }
  });
})();
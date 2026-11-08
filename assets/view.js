CTFd._internal.challenge.data = undefined;

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.renderer = null;

CTFd._internal.challenge.preRender = function() {};

// TODO: Remove in CTFd v4.0
CTFd._internal.challenge.render = null;

// Plain DOM only: works with both the core theme (Alpine, Bootstrap 5) and
// older jQuery themes such as pixo (Bootstrap 4).

// Shared across challenge loads so reopening a challenge never stacks timers
var delayedResultTimer = window.delayedResultTimer || { id: null };
window.delayedResultTimer = delayedResultTimer;

function stopDelayedResultCountdown() {
  if (delayedResultTimer.id !== null) {
    clearInterval(delayedResultTimer.id);
    delayedResultTimer.id = null;
  }
}

function plural(count, unit) {
  return count + " " + unit + (count === 1 ? "" : "s");
}

// Rounds up so students are never told to check back before results are out
function formatRemaining(seconds) {
  var DAY = 86400;
  var HOUR = 3600;
  if (seconds > DAY) {
    return plural(Math.ceil(seconds / DAY), "day");
  }
  if (seconds > HOUR) {
    return plural(Math.ceil(seconds / HOUR), "hour");
  }
  var total = Math.ceil(seconds);
  var minutes = Math.floor(total / 60);
  var secs = plural(total % 60, "second");
  return minutes > 0 ? plural(minutes, "minute") + ", " + secs : secs;
}

function isShown(element) {
  return element.offsetParent !== null;
}

function startDelayedResultCountdown(wait) {
  stopDelayedResultCountdown();

  var display = wait.querySelector(".delayed-result-countdown");
  var expiry = parseInt(wait.dataset.expiry, 10);
  var serverNow = parseInt(wait.dataset.now, 10);
  if (!display || isNaN(expiry) || isNaN(serverNow)) {
    return;
  }

  // Count against the server's clock so a skewed client clock can't
  // trigger a refresh before the server considers the challenge expired
  var loadedAt = Date.now();
  function remaining() {
    return expiry - (serverNow + (Date.now() - loadedAt) / 1000);
  }

  function tick() {
    // Stop once this challenge's view is replaced by another challenge
    if (!wait.isConnected) {
      stopDelayedResultCountdown();
      return;
    }
    // Only act while the message is on screen, so a closed challenge
    // window never reloads the board behind the user
    if (!isShown(wait)) {
      return;
    }
    var left = remaining();
    if (left <= 0) {
      stopDelayedResultCountdown();
      // The URL hash reopens the challenge after the reload
      window.location.reload();
      return;
    }
    display.textContent = formatRemaining(left);
  }

  delayedResultTimer.id = setInterval(tick, 1000);
  tick();
}

// Themes insert the view at different times relative to postRender (the core
// theme renders it on Alpine's next tick), so wait briefly for it to appear
function whenWaitMessageRendered(callback) {
  var attempts = 0;
  (function check() {
    var wait = document.getElementById("delayed-result-wait");
    if (wait) {
      callback(wait);
    } else if (++attempts < 50) {
      setTimeout(check, 50);
    }
  })();
}

CTFd._internal.challenge.postRender = function() {
  stopDelayedResultCountdown();
  whenWaitMessageRendered(function(wait) {
    // Hidden until the user has made a submission
    if (wait.style.display !== "none") {
      startDelayedResultCountdown(wait);
    }
  });
};

// Used by themes that submit through the challenge type (e.g. pixo). The core
// theme posts attempts itself, so there the message appears on the next open.
CTFd._internal.challenge.submit = function(preview) {
  var challenge_id = parseInt(document.getElementById("challenge-id").value);
  var submission = document.getElementById("challenge-input").value;

  var body = {
    challenge_id: challenge_id,
    submission: submission
  };
  var params = {};
  if (preview) {
    params["preview"] = true;
  }

  return CTFd.api.post_challenge_attempt(params, body).then(function(response) {
    if (response.status === 429) {
      // User was ratelimited but process response
      return response;
    }
    if (response.status === 403) {
      // User is not logged in or CTF is paused.
      return response;
    }

    // A held submission comes back as "incorrect". On the first one this load,
    // reveal the wait message and start the timer
    var held = response.data && response.data.status === "incorrect";
    var wait = document.getElementById("delayed-result-wait");
    if (held && wait && wait.style.display === "none") {
      wait.style.display = "";
      startDelayedResultCountdown(wait);
    }
    return response;
  });
};

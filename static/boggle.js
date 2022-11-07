const game_url = "http://127.0.0.1:5000";
const game_api = `${game_url}/api/`;

const num_of_min = 1;

let score = 0;

const already_played_words = new Set();

const load_result = {
  ok: {
    resultValue: "valid",
    scoreToggle: 1,
    comma: "",
  },
  "not-on-board": {
    resultValue: "not-on-board",
    scoreToggle: -1,
    comma: "",
  },
  "not-word": {
    resultValue: "not-a-word",
    scoreToggle: -1,
    comma: "",
  },
};

async function when_game_is_over() {
  $("#submit-guess").prop("disabled", true);

  const for_valid_words = $("#words-valid").text();
  const for_words_not_on_board = $("#words-not-on-board").text();
  const is_not_a_word = $("#words-not-a-word").text();

  await saveGame(score, for_valid_words, for_words_not_on_board, is_not_a_word);

  window.location = `${game_url}/game_over`;
}

function startTimer(duration, display) {
  let start = Date.now();
  let diff;
  let minutes;
  let seconds;

  let throughOnce = false;

  function timer() {
    diff = duration - (((Date.now() - start) / 1000) | 0);

    minutes = (diff / 60) | 0;
    seconds = diff % 60 | 0;

    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;

    display.textContent = minutes + ":" + seconds;

    if (diff <= 0) {
      clearInterval(intervalHandle);
      display.textContent = "00:00";
      when_game_is_over();
    }
  }

  timer();
  let intervalHandle = setInterval(timer, 1000);
}

async function saveGame(
  gameScore,
  for_valid_words,
  for_words_not_on_board,
  is_not_a_word
) {
  const res = await axios.put(`${game_api}save_game`, {
    params: {
      score: gameScore,
      words_valid: for_valid_words,
      words_not_on_board: for_words_not_on_board,
      words_not_a_word: is_not_a_word,
    },
  });
}

async function checkWord(guess) {
  results_holder = {
    statusIsOK: null,
    result: null,
    message: null,
  };

  try {
    const res = await axios.get(`${game_api}check_word?word=${guess}`);

    if (res.status === 200) {
      results_holder["statusIsOK"] = true;
      results_holder["result"] = res.data.result["result"];
    } else {
      results_holder["statusIsOK"] = false;
      results_holder[
        "message"
      ] = `Status was not 200 (OK). response code = ${res.status}. Word to check: '${guess}'`;
    }
  } catch (e) {
    results_holder["statusIsOK"] = false;
    results_holder[
      "message"
    ] = `An unexpected error (${e.message}) occurred while connecting to game server. Word to check: '${guess}'`;
  }

  return results_holder;
}

function postMessage(msg, for_class) {
  $("#messages").removeClass();
  $("#messages").addClass(for_class).text(msg);
}

function guessIsValid(guess) {
  postMessage("", "");

  let validator = new RegExp("^[a-zA-Z]{3,}");

  if (validator.test(guess)) {
    if (already_played_words.has(guess)) {
      postMessage(`'${guess}' was already guessed.`, "error");

      return false;
    } else {
      return true;
    }
  } else {
    postMessage(
      `'${guess}' must be at least 3 alphabetical characters (a - z, A - Z) without embedded spaces.`,
      "error"
    );
    return false;
  }
}

async function handleGuess(event) {
  event.preventDefault();

  let guess = $("#guess").val().toUpperCase().trim();

  if (guessIsValid(guess)) {
    already_played_words.add(guess);

    wordCheck = await checkWord(guess);

    if (wordCheck.statusIsOK) {
      $("#all-guesses").removeClass("hidden");

      let resultValue = load_result[wordCheck.result]["resultValue"];

      $(`#list-${resultValue}`).removeClass("hidden");
      $(`#words-${resultValue}`).text(
        `${$(`#words-${resultValue}`).text()}${
          load_result[wordCheck.result]["comma"]
        }${guess}`
      );

      score =
        score + guess.length * load_result[wordCheck.result]["scoreAdjustor"];
      $("#score").text(`Score: ${score}`);
      load_result[wordCheck.result]["comma"] = ", ";
    } else {
      postMessage(wordCheck.message, "error");
    }
  }

  $("#guess").val("");
}

function visibility_of_words() {
  for (obj_key of Object.keys(load_result)) {
    let resultValue = load_result[obj_key]["resultValue"];
    if ($(`#words-${resultValue}`).text().length > 0) {
      $(`#list-${resultValue}`).removeClass("hidden");

      $("#all-guesses").removeClass("hidden");
    }
  }
}

async function newGame() {
  window.location = game_url;
}

$(function () {
  if ($("#submit-guess").length === 1) {
    let duration = 60 * num_of_min;

    const display = document.querySelector("#time");
    startTimer(duration, display);

    $("#submit-guess").on("click", handleGuess);
  } else {
    if ($("#new-game").length === 1) {
      visibility_of_words();
      postMessage("< < <  GAME   OVER  > > >", "game-over");

      $("#guess").prop("disabled", true);

      $("#new-game").on("click", newGame);
    }
  }
});

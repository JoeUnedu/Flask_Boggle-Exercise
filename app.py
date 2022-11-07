import pdb
from flask import Flask, request, render_template, redirect, flash, session, make_response, jsonify
from flask import session
from boggle import Boggle



boggle_game = Boggle()


app = Flask(__name__)
app.secret_key = "supper secret"
app.config['SECRET_KEY'] =  app.secret_key


app.config.update(
    Set_Session_for_Cookie=True,
    set_session_cookie_site='Lax'
)



session_for_games = "boggle_session"

infor_for_gameover = "boggle_gameover"

num_plays_for_cookies = "boggle_plays"
high_score_for_cookies = "boggle_high"
expiration_for_cookies = 4320000  

G_CK = "cookie_data"
G_CK_PLAYS = "nbr_of_plays"
G_CK_SCORE_HIGH = "score_high"
G_CK_HIGH_IS_NEW = "score_high_is_new"

G_GO = "game_over_data"
G_GO_SCORE = "score"
G_GO_WDS_VALID = "words_valid"
G_GO_WDS_NOT_ON_BOARD = "words_not_on_board"
G_GO_WDS_NOT_WORD = "words_not_a_word"


def set_session_cookie(session_key, value):
    """ Function sets the session cookie with key session_key and
        value.
    """

    session[session_key] = value


def get_cookie_data():
    """ function reads the cookies COOKIE_NBR_PLAYS and COOKIE_HIGH_SCORE and returns 
        the following object with the data from the cookies:
        
    """

    cookie_data = {}
    plays = request.cookies.get(num_plays_for_cookies, "0")
    high = request.cookies.get(high_score_for_cookies, "0")

    cookie_data[G_CK_PLAYS] = int(plays) if (plays.isnumeric()) else 0
    cookie_data[G_CK_SCORE_HIGH] = int(high) if (high.isnumeric()) else 0

    return cookie_data


def get_raw_game_board():
    """ Function calls boggle_game.make_board() to get the lists of 
        random letters for the game board. The raw lists are immediately 
        saved to the session cookie.
    """
    game_board_raw = boggle_game.make_board()
    set_session_cookie(session_for_games, game_board_raw)


def update_cookie_data(score_last_game):
    """ update_cookie_data gets the cookie data and:
        - updates the number of plays by one 
        - checks whether a new high score was achieved. 

      

    """
    cookie_data = get_cookie_data()

    cookie_data[G_CK_PLAYS] = cookie_data[G_CK_PLAYS] + 1

    # check for and update high score as necessary
    if (score_last_game > cookie_data[G_CK_SCORE_HIGH]):
        # We have a new high score
        cookie_data[G_CK_HIGH_IS_NEW] = True
        cookie_data[G_CK_SCORE_HIGH] = score_last_game
    else:
        cookie_data[G_CK_HIGH_IS_NEW] = False

    return cookie_data


def create_game_board_html(game_board_raw):
    """ function creates the Boggle game board html from the raw board data.

        function returns a string html table with the letters.

    """

    if(len(game_board_raw) > 0):
        delim = "</td><td>"
        board = ""
        for row in game_board_raw:
            board = board + f"    		  <tr><td>{(delim).join(row)}</td></tr>\n"
      
        board = f'<table class="tbl-game" id="boggle-board">\n{board}\n		    </table>'
        return board
    else:
        return ""


def assemble_game_data(for_game_end):
    """ function assembles the data needed for the game board in one dictionary. The 
        dictionary may be composed of sub-dictionairies, but the goal is to have it 
        all in one place.

        
    """


    game = {
        "board": {},
        G_CK: {},
        "button_attr": {},
        "data_is_good": True
    }

    game["board"]["raw"] = session.get(session_for_games, "")
    game["board"]["html"] = create_game_board_html(game["board"]["raw"])

    if (for_game_end):
        game_over_data = session.get(infor_for_gameover, "")
        if (len(game_over_data) > 0):
           
            set_session_cookie(infor_for_gameover, "")

           
            game[G_GO] = game_over_data["params"]

           
            game[G_CK] = update_cookie_data(game[G_GO][G_GO_SCORE])
          

            if (game[G_CK][G_CK_HIGH_IS_NEW]):
             
                game["flash"] = []
                game["flash"].append({
                    "msg_text": "&#x1F601; CONGRATULATIONS -- A new high score &#x1F601;",
                    "msg_class": "high-score"
                })

            game["button_attr"] = {
                "id": "new-game",
                "text": "Start New Game"
            }
        else:
          
            game["data_is_good"] = False

    else:

   
        game[G_GO] = {}

        game[G_CK] = get_cookie_data()
       

        game["button_attr"] = {
            "id": "submit-guess",
            "text": "Guess"
        }

    return game


@ app.route("/")
def game_welcome():
    """ Renders a welcome page with the boggle game board.

    """

    get_raw_game_board()


    game = assemble_game_data(False)

    html = render_template("game.html", game_board=game["board"]["html"],
                           button_attr=game["button_attr"],
                           scoring=game[G_CK],
                           score=0,
                           words_played=game[G_GO])

    resp_obj = make_response(html)

    resp_obj.set_cookie(
        high_score_for_cookies, str(game[G_CK][G_CK_SCORE_HIGH]), expiration_for_cookies, None, "/", None, False, False, "Lax")
    resp_obj.set_cookie(
        num_plays_for_cookies, str(game[G_CK][G_CK_PLAYS]), expiration_for_cookies, None, "/", None, False, False, "Lax")
    return resp_obj


@ app.route("/api/check_word")
def check_word():
    """ Checks the word passed in to ensure it is a valid word and that
        the word exists on the current game board.

        

    """

    word_guess = request.args.get("word", "")
    word_guess_valid = {}

    game_board = session[session_for_games]

    word_guess_valid["result"] = boggle_game.check_valid_word(
        game_board, word_guess)

    return jsonify({"result": word_guess_valid})


@ app.route("/api/save_game", methods=["PUT"])
def handle_save_game():
    """ takes the score, valid words, not on board, and not a word lists and saves
        them in the session cookie.

        

    """

    game_values = request.get_json()
 
    set_session_cookie(infor_for_gameover, game_values)

   
    resp = make_response()

    return resp


@ app.route("/game_over")
def handle_game_over():
    """ handles the game_over. The 'welcome' template is used, but with different 
        button text. 
  

    """


    game = assemble_game_data(True)

    if (game["data_is_good"]):
        # data is good -- data was found in game-over session data. The checks exist to prevent
        #  someone from going directly to root\game-over without ever playing a game.
        if (game[G_CK][G_CK_HIGH_IS_NEW]):
            for msg_data in game["flash"]:
                flash(msg_data["msg_text"], msg_data["msg_class"])

        html = render_template("game.html", game_board=game["board"]["html"],
                               button_attr=game["button_attr"],
                               score=game[G_GO][G_GO_SCORE],
                               scoring=game[G_CK],
                               words_played=game[G_GO])

        resp_obj = make_response(html)
      
        resp_obj.set_cookie(
            num_plays_for_cookies, str(game[G_CK][G_CK_PLAYS]), expiration_for_cookies, None, "/", None, False, False, "Lax")

        if (game[G_CK][G_CK_HIGH_IS_NEW]):
          
            resp_obj.set_cookie(
                high_score_for_cookies, str(game[G_CK][G_CK_SCORE_HIGH]), expiration_for_cookies, None, "/", None, False, False, "Lax")

        return resp_obj

    else:
      
        return redirect("/")

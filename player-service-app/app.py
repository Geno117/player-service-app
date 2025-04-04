from flask import Flask, request, jsonify
import pandas as pd
import sqlite3
from sqlalchemy import create_engine
from player_service import PlayerService
import ollama
from langchain.tools import Tool
from langchain_ollama import ChatOllama
import json

app = Flask(__name__)

# Load CSV file in pandas dataframe and create SQLite database
df = pd.read_csv('Player.csv')
engine = create_engine('sqlite:///player.db', echo=True)
df.to_sql('players', con=engine, if_exists='replace', index=False)

queries = {
    "What are the details of a player given their playerId?": 
        "SELECT * FROM players WHERE playerId = ?;",
    
    "How many players were born in a specific country?": 
        "SELECT birthCountry, COUNT(*) FROM players WHERE birthCountry = ? GROUP BY birthCountry;",
    
    "Which player is the tallest?": 
        "SELECT playerId, nameFirst, nameLast, height FROM players ORDER BY height DESC LIMIT 1;",
    
    "Which player is the heaviest?": 
        "SELECT playerId, nameFirst, nameLast, weight FROM players ORDER BY weight DESC LIMIT 1;",
    
    "How many players were born in each state?": 
        "SELECT birthState, COUNT(*) FROM players GROUP BY birthState ORDER BY COUNT(*) DESC;",
    
    "How many players were born in each country?": 
        "SELECT birthCountry, COUNT(*) FROM players GROUP BY birthCountry ORDER BY COUNT(*) DESC;",
    
    "Which player lived the longest?": 
        "SELECT playerId, nameFirst, nameLast, (deathYear - birthYear) AS lifespan FROM players WHERE deathYear IS NOT NULL ORDER BY lifespan DESC LIMIT 1;",
    
    "Who is the youngest player ever recorded?": 
        "SELECT playerId, nameFirst, nameLast, birthYear, birthMonth, birthDay FROM players ORDER BY birthYear DESC, birthMonth DESC, birthDay DESC LIMIT 1;",
    
    "Who is the oldest player ever recorded?": 
        "SELECT playerId, nameFirst, nameLast, birthYear, birthMonth, birthDay FROM players ORDER BY birthYear ASC, birthMonth ASC, birthDay ASC LIMIT 1;",
    
    "Which players are still alive?": 
        "SELECT playerId, nameFirst, nameLast FROM players WHERE deathYear IS NULL;",
    
    "How many players debuted in a given year?": 
        "SELECT COUNT(*) FROM players WHERE strftime('%Y', debut) = ?;",
    
    "Which players debuted in a specific year?": 
        "SELECT playerId, nameFirst, nameLast FROM players WHERE strftime('%Y', debut) = ?;",
    
    "Which players retired in a specific year?": 
        "SELECT playerId, nameFirst, nameLast FROM players WHERE strftime('%Y', finalGame) = ?;",
    
    "How many players batted right-handed vs. left-handed?": 
        "SELECT bats, COUNT(*) FROM players GROUP BY bats;",
    
    "How many players threw right-handed vs. left-handed?": 
        "SELECT throws, COUNT(*) FROM players GROUP BY throws;",
    
    "Who was the heaviest player born in a specific country?": 
        "SELECT playerId, nameFirst, nameLast, weight FROM players WHERE birthCountry = ? ORDER BY weight DESC LIMIT 1;",
    
    "Who was the tallest player born in a specific country?": 
        "SELECT playerId, nameFirst, nameLast, height FROM players WHERE birthCountry = ? ORDER BY height DESC LIMIT 1;",
    
    "What is the average height and weight of players?": 
        "SELECT AVG(height) AS avg_height, AVG(weight) AS avg_weight FROM players;",
    
    "Which players share the same first and last name?": 
        "SELECT nameFirst, nameLast, COUNT(*) FROM players GROUP BY nameFirst, nameLast HAVING COUNT(*) > 1;",
    
    "Which year had the most player debuts?": 
        "SELECT strftime('%Y', debut) AS debutYear, COUNT(*) FROM players GROUP BY debutYear ORDER BY COUNT(*) DESC LIMIT 1;"
}

all_supported_queries = ",".join([i for i in queries])
prompt = f"if the user query fits any of these questions, return the questions else return -1"
prompt = f"figure out what variable needs to replace the placeholder given this sql query and this user response."

# Get all players
@app.route('/v1/players', methods=['GET'])
def get_players():
    player_service = PlayerService()
    result = player_service.get_all_players()
    return result

@app.route('/v1/players/<string:player_id>')
def query_player_id(player_id):
    player_service = PlayerService()
    result = player_service.search_by_player(player_id)

    if len(result) == 0:
        return jsonify({"error": "No record found with player_id={}".format(player_id)})
    else:
        return jsonify(result)

@app.route('/v1/chat/list-models')
def list_models():
    return jsonify(ollama.list())

@app.route('/v1/chat', methods=['POST'])
def chat():
    # Process the data as needed
    debug_info = {}
    data = request.get_json()
    print(f"emeng {data}")
    print(f"emeng {type(data)}")
    user_query = data.get("message", "")
    debug_info["user_query"]=user_query

    predicted_query = get_query_from_ollama(user_query)
    debug_info["predicted_query"]=predicted_query
    if predicted_query:
        return handle_user_query(predicted_query)

    return debug_info, 500

    # prompt = f"Answer with 1 word. What is the country the player is interested in? user query: {user_query}"
    # prompt = f"Extract and return exactly one word, the country name from this query: {user_query}"
    # resp  = ollama.generate(model="tinyllama", prompt=prompt)


    find_country_chat = [
        {"role": "system",
        "message": "return single word for the country involved"},
        {"role": "user",
        "message": user_query}
    ]
    resp = ollama.chat(model="tinyllama", messages = find_country_chat)
    print(resp['message']['content'])
    player_service = PlayerService()
    return player_service.search_by_country(resp['message']['content'])

    # use ollama to pick out the player user is interested in 
    # prompt = f"if the user query fits any of these questions, return the questions else return -1. possible answerable queries: {all_supported_queries}.user query: {user_query}"
    # prompt = f"which question answers this user question: {user_query}. list of questions: {all_supported_queries}"
    # resp  = ollama.generate(model="tinyllama", prompt=prompt)
    # print(resp)
    # user_question = resp.response
    # print(user_question)
    # if user_question in queries:
    #     prompt  = f"Based on this user question, {user_query}, and this sql query {queries[user_question]} what is the missing value needed and if none are needed for the sql query than return -1."
    #     resp = ollama.generate(model="tinyllama", prompt=prompt)
    #     answer = None
    #     placeholder = resp.response if resp.response != "-1" else None
    #     player_service = PlayerService()
    #     return player_service.search_by_query(queries[user_question], placeholder)
    # else:
    #     return jsonify({"user_query": user_query, "user_question": user_question})


    
    return jsonify({"hello": 1}), 200

llm = ChatOllama(model="tinyllama")
def get_query_from_ollama(user_input):
    prompt = f"""
    You are a database assistant. Given a user's natural language question, determine the most appropriate SQL query to execute.
    
    - Respond in JSON format:
    {{
        "query_name": "Best matching query from list",
        "parameters": ["Extracted parameters if needed"]
    }}

    Queries available:
    {list(queries.keys())}

    User: {user_input}
    """
    response = llm.invoke(prompt)
    print(response)
        
    # Parse JSON response
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        return None
    
def handle_user_query(user_query):
    query_info = get_query_from_ollama(user_query)
    
    if not query_info:
        return "Failed to parse query selection."

    query_name = query_info.get("query_name")
    parameters = query_info.get("parameters", [])

    results = execute_query(query_name, parameters)
    return results

def execute_query(query_name, parameters):
    # Connect to the SQLite database
    conn = sqlite3.connect("players.db")  # Adjust for your database
    cursor = conn.cursor()

    sql_query = queries.get(query_name)
    if not sql_query:
        return "Invalid query selection."

    # Execute SQL query
    cursor.execute(sql_query, parameters)
    results = cursor.fetchall()

    # Close connection
    conn.close()
    
    return results



def test_queries(db_path='player.db'):
    queries = {
        "What are the details of a player given their playerId?": 
            ("SELECT * FROM players WHERE playerId = ?;", ("aaronha01",)),
        
        "How many players were born in a specific country?": 
            ("SELECT birthCountry, COUNT(*) FROM players WHERE birthCountry = ? GROUP BY birthCountry;", ("USA",)),
        
        "Which player is the tallest?": 
            ("SELECT playerId, nameFirst, nameLast, height FROM players ORDER BY height DESC LIMIT 1;", ()),
        
        "Which player is the heaviest?": 
            ("SELECT playerId, nameFirst, nameLast, weight FROM players ORDER BY weight DESC LIMIT 1;", ()),
        
        "How many players were born in each state?": 
            ("SELECT birthState, COUNT(*) FROM players GROUP BY birthState ORDER BY COUNT(*) DESC;", ()),
        
        "How many players were born in each country?": 
            ("SELECT birthCountry, COUNT(*) FROM players GROUP BY birthCountry ORDER BY COUNT(*) DESC;", ()),
        
        "Which player lived the longest?": 
            ("SELECT playerId, nameFirst, nameLast, (deathYear - birthYear) AS lifespan FROM players WHERE deathYear IS NOT NULL ORDER BY lifespan DESC LIMIT 1;", ()),
        
        "Who is the youngest player ever recorded?": 
            ("SELECT playerId, nameFirst, nameLast, birthYear, birthMonth, birthDay FROM players ORDER BY birthYear DESC, birthMonth DESC, birthDay DESC LIMIT 1;", ()),
        
        "Who is the oldest player ever recorded?": 
            ("SELECT playerId, nameFirst, nameLast, birthYear, birthMonth, birthDay FROM players ORDER BY birthYear ASC, birthMonth ASC, birthDay ASC LIMIT 1;", ()),
        
        "Which players are still alive?": 
            ("SELECT playerId, nameFirst, nameLast FROM players WHERE deathYear IS NULL;", ()),
        
        "How many players debuted in a given year?": 
            ("SELECT COUNT(*) FROM players WHERE strftime('%Y', debut) = ?;", ("2004",)),
        
        "Which players debuted in a specific year?": 
            ("SELECT playerId, nameFirst, nameLast FROM players WHERE strftime('%Y', debut) = ?;", ("2004",)),
        
        "Which players retired in a specific year?": 
            ("SELECT playerId, nameFirst, nameLast FROM players WHERE strftime('%Y', finalGame) = ?;", ("2015",)),
        
        "How many players batted right-handed vs. left-handed?": 
            ("SELECT bats, COUNT(*) FROM players GROUP BY bats;", ()),
        
        "How many players threw right-handed vs. left-handed?": 
            ("SELECT throws, COUNT(*) FROM players GROUP BY throws;", ()),
        
        "Who was the heaviest player born in a specific country?": 
            ("SELECT playerId, nameFirst, nameLast, weight FROM players WHERE birthCountry = ? ORDER BY weight DESC LIMIT 1;", ("USA",)),
        
        "Who was the tallest player born in a specific country?": 
            ("SELECT playerId, nameFirst, nameLast, height FROM players WHERE birthCountry = ? ORDER BY height DESC LIMIT 1;", ("USA",)),
        
        "What is the average height and weight of players?": 
            ("SELECT AVG(height) AS avg_height, AVG(weight) AS avg_weight FROM players;", ()),
        
        "Which players share the same first and last name?": 
            ("SELECT nameFirst, nameLast, COUNT(*) FROM players GROUP BY nameFirst, nameLast HAVING COUNT(*) > 1;", ()),
        
        "Which year had the most player debuts?": 
            ("SELECT strftime('%Y', debut) AS debutYear, COUNT(*) FROM players GROUP BY debutYear ORDER BY COUNT(*) DESC LIMIT 1;", ())
    }

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for description, (query, params) in queries.items():
        print(f"\n--- {description} ---")
        try:
            cursor.execute(query, params)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            result_df = pd.DataFrame(rows, columns=col_names)
            print(result_df)
        except Exception as e:
            print(f"Error running query: {e}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)




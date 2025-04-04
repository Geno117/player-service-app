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

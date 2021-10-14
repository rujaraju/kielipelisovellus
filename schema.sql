CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    username TEXT,
    firstname TEXT,
    lastname TEXT,
    passw TEXT,
    authority INTEGER,
    active BOOLEAN DEFAULT true
);

CREATE TABLE lang (
    id SERIAL PRIMARY KEY,
    langname TEXT
);

CREATE TABLE game (
    id SERIAL PRIMARY KEY,
    gamename TEXT, 
    lang_id INTEGER REFERENCES lang,
    creator_id INTEGER REFERENCES user,
    playcount INTEGER DEFAULT 0,
    visible BOOLEAN DEFAULT True
);

CREATE TABLE sentence (
    id SERIAL PRIMARY KEY,
    info TEXT,
    rightanswer TEXT,
    games_id INTEGER REFERENCES game
);

CREATE TABLE points (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user,
    game_id INTEGER REFERENCES game,
    points INTEGER
);

CREATE TABLE school (
    id SERIAL PRIMARY KEY,
    schoolname TEXT,
    info TEXT,
    ADDRESS TEXT,
    PHONE TEXT,
    www TEXT,
    visible BOOLEAN
);

CREATE TABLE schooladmin (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user,
    school_id INTEGER REFERENCES school
);

CREATE TABLE course (
    id SERIAL PRIMARY KEY,
    coursename TEXT,
    info TEXT,
    school_id INTEGER REFERENCES school,
    visible BOOLEAN DEFAULT true
);

CREATE TABLE coursegame (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES game,
    course_id INTEGER REFERENCES course
);

CREATE TABLE awaitingapproval (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user,
    wantsauthority INTEGER
)
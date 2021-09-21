CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT,
    firstname TEXT,
    lastname TEXT,
    passw TEXT,
    authority INTEGER,
    points INTEGER
);

CREATE TABLE langs (
    id SERIAL PRIMARY KEY,
    langname TEXT
);

CREATE TABLE games (
    id SERIAL PRIMARY KEY,
    gamename TEXT, 
    lang_id INTEGER REFERENCES langs,
    visible BOOLEAN
);

CREATE TABLE sentences (
    id SERIAL PRIMARY KEY,
    info TEXT,
    rightanswer TEXT,
    created_at TIMESTAMP,
    games_id INTEGER REFERENCES games
);

CREATE TABLE points (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    game_id INTEGER REFERENCES games,
    points INTEGER
);

CREATE TABLE schools (
    id SERIAL PRIMARY KEY,
    schoolname TEXT,
    info TEXT,
    ADDRESS TEXT,
    PHONE TEXT,
    www TEXT,
    visible BOOLEAN
);

CREATE TABLE schooladmins (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users,
    school_id INTEGER REFERENCES schools
);

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    coursename TEXT,
    info TEXT,
    school_id INTEGER REFERENCES schools,
    visible BOOLEAN
);

CREATE TABLE coursegames (
    id SERIAL PRIMARY KEY,
    game_id INTEGER REFERENCES games,
    course_id INTEGER REFERENCES courses
);
CREATE TABLE Merkit (
    id SERIAL PRIMARY KEY, 
    nimi TEXT, 
);

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE,
    password TEXT
);

CREATE TABLE usersTOmerkit (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    merkki_id INTEGER REFERENCES Merkit(id),  
);
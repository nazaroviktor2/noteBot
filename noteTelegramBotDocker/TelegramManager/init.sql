
create table IF NOT EXISTS users
(
    id integer not null primary key,
    name text

);
create table IF NOT EXISTS  note
(
    id serial NOT NULL primary key ,
    user_id integer references users(id) NOT NULL,
    id_for_user integer NOT NULL,
    text text  NOT NULL,
    date date NOT NULL

);

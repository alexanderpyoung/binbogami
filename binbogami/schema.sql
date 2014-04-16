drop table if exists users;
drop table if exists podcasts_header;
drop table if exists podcasts_casts;
drop table if exists podcasts_categories;

create table users (
    id integer primary key autoincrement,
    username text not null,
    name text not null,
    pwhash text not null,
    storage real,
    bandwidth real
);

create table podcasts_header (
    id integer primary key autoincrement,
    owner integer not null,
    name text not null,
    description text not null,
    url text not null,
    image text not null,
	categories text not null,
    foreign key(owner) references users(id)
); 

create table podcasts_casts (
    id integer primary key autoincrement,
    podcast integer not null,
    title text not null,
    description text not null,
    castfile text not null,
	date text not null,
	length text not null,
	filetype text not null,
    foreign key(podcast) references podcasts_header(id)
);

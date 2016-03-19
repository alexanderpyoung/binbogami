drop table if exists users cascade;
drop table if exists podcasts_header cascade;
drop table if exists podcasts_casts cascade;
drop table if exists podcasts_categories cascade;
drop table if exists stats_xml cascade;
drop table if exists stats_episodes cascade;

create table users (
    id serial primary key,
    username text not null,
    name text not null,
    pwhash text not null,
    email text not null,
    storage real,
    bandwidth real
);

create table podcasts_header (
    id serial primary key,
    owner integer references users (id),
    name text not null,
    description text not null,
    url text not null,
    image text not null,
    categories text not null,
    explicit text not null
);

create table podcasts_casts (
    id serial primary key,
    podcast integer references podcasts_header (id),
    title text not null,
    description text not null,
    castfile text,
  	date timestamp with time zone not null,
	  length text not null,
	  filetype text not null,
    casturl text
);

create table stats_xml (
    id serial primary key,
    podcast integer not null references podcasts_header (id),
    date timestamp with time zone not null,
    ip text not null, 
    referrer text
);

create table stats_episodes (
    id serial primary key,
    podcast integer references podcasts_header (id),
    podcast_episode integer references podcasts_casts (id),
    date timestamp with time zone not null,
    ip text not null,
    referrer text
);

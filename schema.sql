drop table if exists users;
create table users (
  id integer primary key autoincrement,
  username text not null,
  password text not null,
  display_name text,
  profile_pic text,
  about text
);

drop table if exists costumes;
create table costumes (
  id integer primary key autoincrement,
  'name' text not null,
  'series' text not null,
  'variant' text,
  'notes' text not null,
  'year' integer,
  'status' text,
  'cover' text,
  'slug' text unique not null,
   cosplayer integer not null,
  foreign key(cosplayer) references users(id)
);

drop table if exists images;
create table images (
  id integer primary key autoincrement,
  'filename' text not null,
  'type' text not null,
  'order' integer,
  costume_id integer not null,
  foreign key(costume_id) references costumes(id)
);

drop table if exists components;
create table components (
  id integer primary key autoincrement,
  'name' text not null,
  'text' text not null,
  costume_id integer not null,
  foreign key(costume_id) references costumes(id)
);

drop table if exists tutorials;
create table tutorials (
  id integer primary key autoincrement,
  'title' text not null,
  'content' text not null,
  'slug' text not null,
  author integer not null,
  foreign key(author) references users(id)
);

drop table if exists updates;
create table updates (
  id integer primary key autoincrement,
  'datetime' timestamp not null,
  'message' text not null
  );
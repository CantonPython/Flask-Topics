drop table if exists user;
create table user (
  user_id integer primary key autoincrement,
  username text not null,
  email text not null,
  passwd text not null
);

drop table if exists topic;
create table topic (
  id integer primary key autoincrement,
  author_id integer not null,
  description text not null,
  votes integer default 0,
  post_date integer
);

drop table if exists user_topic;
create table user_topic (
  user_id integer not null,
  topic_id integer not null
)

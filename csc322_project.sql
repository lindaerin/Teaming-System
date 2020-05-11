DROP DATABASE IF EXISTS csc322_project;
CREATE DATABASE csc322_project;
use csc322_project;


-- create a table for all applications
CREATE TABLE tb_applied ( 
	user_id INT AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
	email VARCHAR(100) NOT NULL ,
    interest VARCHAR(50) NOT NULL,
    credential VARCHAR(50) NOT NULL,
    reference VARCHAR(50) NOT NULL,
    message text, 
	PRIMARY KEY (user_id)
	);
    
-- insert test data for applied
insert into tb_applied (username, email,interest,credential,reference) values 
('Masuda Farehia', 'mfarehia@gmail.com', 'Science', 'Student at CCNY', 'Jie Wie'),
('Jie', 'jie@gmail.com', 'Hello', 'Student at WOrld', 'Masuda'),
('Linda Erin', 'linda@yahoo.com', 'CS', 'Local Bum', 'N/A');
    
--  create table user
CREATE TABLE tb_user ( 
	user_id INT AUTO_INCREMENT,
    user_name VARCHAR(50) NOT NULL,
    user_password VARCHAR(50) NOT NULL ,
	email VARCHAR(100) NOT NULL ,
    didtheychangepass BOOLEAN NOT NULL DEFAULT 0 ,
    interest VARCHAR(50) ,
    credential VARCHAR(50),
	PRIMARY KEY (user_id)
	);
    
-- setting user_id auto increment from 100
ALTER TABLE tb_user AUTO_INCREMENT = 100;

insert into tb_user (user_name, user_password,  email, didtheychangepass) values 
('admin', 'admin','admin' ,'1'),
('test1', '1', 'www.111@111.com' , '0'),
('test2','1','www.222@222.com' ,'0'),
('test3','1', 'www.333@333.com', '0'), 
('test4','1', 'www.444@444.com','0'),
('Bob','1', 'bob@email.com' , '0' ),
('Jane', '1', 'jane@email.com' , '0'),
('CSGod', '1', 'h3ckz@email.com', '0');


CREATE TABLE tb_blacklist ( 
    email VARCHAR(100) NOT NULL 
    );

-- create table profile
create table tb_profile (
	user_id INT,
    user_type varchar (50)  default 'Ordinary',   -- 3 tpyes of users ordinary user, VIP, Super User,       -- 3 tpyes of users ordinary user, VIP, Super User 
    user_scores INT default 0,    -- user scores  default 0
    user_status bit default 1,    -- only 0 or 1;  1 means good standing, 0 means have been banned(into black list) 
    foreign key (user_id) references tb_user (user_id)
    );

insert into tb_profile (user_id, user_type, user_scores) values
(100,'Super User', 100),
(101, 'Ordinary', 20),
(102, 'Ordinary', 10),
(103, 'SuperUser', 30),
(104, 'SuperUser', 25),
(105, 'Ordinary', 5),
(106, 'SuperUser',35);

create table tb_whitelist (
    user_id INT,
    user_name_friend VARCHAR(50),
    foreign key (user_id) references tb_user (user_id)
    );

create table tb_user_blacklist (
    user_id INT,
    user_name_blocked VARCHAR(50),
    foreign key (user_id) references tb_user (user_id)
    );

create table tb_invite (
    user_id INT,
    group_id INT,
    foreign key (user_id) references tb_user (user_id)
    );
    
-- create table taboo word   
create table tb_taboo (
	word_id int auto_increment,
    word varchar(100) unique,
    primary key (word_id)
);
ALTER TABLE tb_taboo auto_increment = 1;

-- insert value in table taboo
insert into tb_taboo (word_id, word) values
(1, 'fuck'),
(2, 'stupid'),
(3, 'shit'),
(4, 'fk');

-- create table user taboo 
create table tb_user_taboo (
	user_id int,
    word varchar(100),
    foreign key (user_id) references tb_user (user_id)
);


-- create table post
create table tb_post (
	post_id int auto_increment,
    user_id int not null,
    post_title varchar (100),
    post_content text,
    post_time timestamp default current_timestamp,
    primary key (post_id),
    foreign key (user_id) references tb_user (user_id)
	);
    
ALTER TABLE tb_post AUTO_INCREMENT = 500;

-- create table reply
create table tb_reply (
	reply_id int auto_increment,
    post_id int,
    user_id int,
    reply_content text,
    reply_time timestamp default current_timestamp,
    primary key (reply_id),
    foreign key (user_id) references tb_user (user_id),
    foreign key (post_id) references tb_post (post_id) ON delete cascade
	);
ALTER TABLE tb_reply AUTO_INCREMENT = 500;

-- create table team 
create table tb_group (
	group_id int auto_increment,
    group_name varchar(50),
    group_describe text,
    group_created_time timestamp default current_timestamp,
    user_id int,
    primary key (group_id),
    foreign key (user_id) references tb_user (user_id)
	);
  
ALTER TABLE tb_group AUTO_INCREMENT = 1000;  

insert into tb_group (group_id, group_name, group_describe, user_id) values
(1000, 'GROUP_TEST', 'This is for group test', '104');  

create table tb_group_members (
	group_id int,
    user_name varchar(50),
    foreign key (group_id) references tb_group (group_id)
);

insert into tb_group_members (group_id, user_name) values
(1000, 'test4');


-- create table chat
create table tb_chat (
	user_id int,
    group_id int,
    chat_content text,
    chat_time timestamp default current_timestamp,
    foreign key (user_id) references tb_user (user_id),
    foreign key (group_id) references tb_group (group_id)
);

-- POLLING SYSTEM
create table tb_poll (
	poll_id int auto_increment,
    poll_title varchar(50),
    poll_body varchar(100),
    poll_status int default 1,
    created_by int,
    poll_creation timestamp default current_timestamp,
    group_id int,
    primary key (poll_id),
    foreign key (group_id) references tb_group (group_id),
    foreign key (created_by) references tb_user (user_id)
);

create table tb_poll_options (
	option_id int auto_increment,
    poll_id int,
    optionText varchar(50),
    foreign key (poll_id) references tb_poll (poll_id),
    primary key (option_id)
);

create table tb_poll_responses (
	response_id int auto_increment,
    poll_id int,
    user_id int,
    option_id int,
    primary key (response_id),
    foreign key (poll_id) references tb_poll (poll_id),
    foreign key (user_id) references tb_user (user_id),
    foreign key (option_id) references tb_poll_options (option_id)
);

-- insert a simple poll into a group
 insert into tb_poll (poll_title, poll_body, group_id, created_by) values 
 ('Programming Language', 'What is your favorite programming language?', 1000, 102);

-- insert poll options
DROP procedure IF EXISTS `insert_poll_options`;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `insert_poll_options`(IN POLL_OPTIONS varchar(1000), IN NEWPOLL int)
BEGIN
	SET @myArrayOfOptions = POLL_OPTIONS;
    WHILE(LOCATE(',', @myArrayOfOptions) > 0) DO
            SET @value = SUBSTRING_INDEX(@myArrayOfOptions,',',1);
            IF (LENGTH(@myArrayOfOptions) > LENGTH(@value) +2)  THEN
                SET @myArrayOfOptions= SUBSTRING(@myArrayOfOptions, LENGTH(@value) + 2);
                INSERT INTO `tb_poll_options` (poll_id, optionText) VALUES(NEWPOLL, @value);
            ELSE
                INSERT INTO `tb_poll_options` (poll_id, optionText) VALUES(NEWPOLL, @value);
                -- to end while loop
                SET @myArrayOfOptions=  '';
            END IF;
            IF LENGTH(@myArrayOfOptions) > 0 AND LOCATE(',', @myArrayOfOptions) = 0 then
                -- Last entry was withóut comma
                INSERT INTO `tb_poll_options` (poll_id, optionText) VALUES(NEWPOLL, @myArrayOfOptions);
            END IF;
    END WHILE;
END$$

DELIMITER ;

CALL insert_poll_options('Python,JavaScript,Ruby,Go,C++', 1);


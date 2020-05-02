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
    interest VARCHAR(50) ,
    credential VARCHAR(50),
	PRIMARY KEY (user_id)
	);
    
-- setting user_id auto increment from 100
ALTER TABLE tb_user AUTO_INCREMENT = 100;

insert into tb_user (user_name, user_password,  email) values 
('admin', 'admin', 'admin'),
('test1', '1', 'www.111@111.com'),
('test2','1','www.222@222.com'),
('test3','1', 'www.333@333.com'), 
('test4','1', 'www.444@444.com'),
('Bob','1', 'bob@email.com'),
('Jane', '1', 'jane@email.com'),
('CSGod', '1', 'h3ckz@email.com');


CREATE TABLE tb_blacklist ( 
	user_id INT AUTO_INCREMENT,
	foreign key (user_id) references tb_user (user_id)
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
(101, 'Ordinary', 0),
(102, 'Ordinary', 0),
(103, 'Ordinary', 0),
(104, 'Ordinary', 0);

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
    foreign key (post_id) references tb_post (post_id)
	);
ALTER TABLE tb_reply AUTO_INCREMENT = 500;

-- create table team 
create table tb_group (
	group_id int auto_increment,
    group_name varchar(50),
    group_describe text,
    group_created_time timestamp default current_timestamp,
    primary key (group_id)
	);
  
ALTER TABLE tb_group AUTO_INCREMENT = 1000;  

create table tb_group_members (
	group_id int,
    user_id int,
    foreign key (group_id) references tb_group (group_id),
    foreign key(user_id) references tb_user(user_id)
);

-- insert test data for team
insert into tb_group (group_name, group_describe) values 
('Blue', 'Blue Vikings FTW!'),
('Red', 'Red Spartans are the Champions'),
('Green', 'Green Leopards are Mighty!'), 
('Teal', 'Teal Tequila');

DROP procedure IF EXISTS `insert_members`;

DELIMITER $$
CREATE DEFINER=`root`@`localhost` PROCEDURE `insert_members`(IN USER_ID varchar(50), IN NEWGROUP int)
BEGIN
	SET @myArrayOfUsers = USER_ID;
    #SET @myArrayOfUsers = '100,101,102';
    #SET @myArrayOfUsers = '106,107,108,';
    WHILE(LOCATE(',', @myArrayOfUsers) > 0) DO
            SET @value = SUBSTRING_INDEX(@myArrayOfUsers,',',1);
            IF (LENGTH(@myArrayOfUsers) > LENGTH(@value) +2)  THEN
                SET @myArrayOfUsers= SUBSTRING(@myArrayOfUsers, LENGTH(@value) + 2);
                INSERT INTO `tb_group_members` VALUES(NEWGROUP, @value);
            ELSE
                INSERT INTO `tb_group_members` VALUES(NEWGROUP, @value);
                -- to end while loop
                SET @myArrayOfUsers=  '';
            END IF;
            IF LENGTH(@myArrayOfUsers) > 0 AND LOCATE(',', @myArrayOfUsers) = 0 then
                -- Last entry was withóut comma
                INSERT INTO `tb_group_members` VALUES(NEWGROUP, @myArrayOfUsers);
            END IF;
    END WHILE;
END$$

DELIMITER ;

CALL insert_members('101,103,102,100', 1001);
CALL insert_members('102,101', 1003);
CALL insert_members('103,101,102', 1000);
CALL insert_members('103,101,100', 1002);

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
('Programming Language', 'What is your favorite programming language?', 1000, 102),
('Feature', 'What feature do you think is most important?', 1001, 103),
('Meeting Times', 'When are you available to meet this week?', 1002, 101);


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
CALL insert_poll_options('Messaging,Notification,Styling', 2);
CALL insert_poll_options('Monday after class,Tuesday 2pm,Wednesday after class', 3);

-- insert poll responses by group_members - vote reponses



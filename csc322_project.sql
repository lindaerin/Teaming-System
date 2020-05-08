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
('CSGod', '1', 'h3ckz@email.com'),
('ModErin', '1', 'vip@email.com'),
('ModGod', '1', 'vip1@email.com');


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
(104, 'Ordinary', 0),
(105, 'Ordinary', 0),
(106, 'Ordinary', 0),
(107, 'Ordinary', 0),
(108, 'VIP', 30),
(109, 'VIP', 90);

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
    group_name varchar(50) NOT NULL,
    group_describe text NOT NULL,
    group_status varchar(50) DEFAULT 'active',
    group_created_time timestamp default current_timestamp,
    primary key (group_id)
	);
  
ALTER TABLE tb_group AUTO_INCREMENT = 1000;  

create table tb_group_members (
	group_id int,
    user_id int,
    user_warnings int default 0,
    user_praises int default 0,
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
                INSERT INTO `tb_group_members` VALUES(NEWGROUP, @value, 0, 0);
            ELSE
                INSERT INTO `tb_group_members` VALUES(NEWGROUP, @value, 0, 0);
                -- to end while loop
                SET @myArrayOfUsers=  '';
            END IF;
            IF LENGTH(@myArrayOfUsers) > 0 AND LOCATE(',', @myArrayOfUsers) = 0 then
                -- Last entry was withóut comma
                INSERT INTO `tb_group_members` VALUES(NEWGROUP, @myArrayOfUsers, 0, 0);
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
    vote_count int default 0,
    highest_vote varchar(100) default NULL,
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

 
-- create groupmember user evaluation system table
CREATE TABLE tb_user_evaluations (
	user_eval_id int auto_increment,
	group_id int NOT NULL,
    rater_id int NOT NULL,
    evaluation_score int NOT NULL,
    user_id int NOT NULL,
    foreign key (group_id) references tb_group(group_id),
    foreign key (rater_id) references tb_user(user_id),
    foreign key (user_id) references tb_user(user_id),
    primary key (user_eval_id)
);

-- create project evaluation system table
CREATE TABLE tb_project_evaluations (
	project_eval_id int auto_increment,
    project_open_reason varchar(100) NOT NULL,
    project_close_reason varchar(100) NOT NULL,
    group_id int NOT NULL,
    project_rating int default NULL,
    evaluator_id int default NULL,
    primary key (project_eval_id),
    foreign key (group_id) references tb_group(group_id),
    foreign key (evaluator_id) references tb_user(user_id)
);

-- create group_vote table - not related to polls / user related votes
CREATE TABLE tb_group_votes (
	group_vote_id int auto_increment,
    group_id int NOT NULL,
    vote_subject varchar(50) NOT NULL,
    user_subject int,
    user_id int NOT NULL,
    highest_vote varchar(50) default NULL,
    vote_count int default 0,
    primary key (group_vote_id),
    foreign key (group_id) references tb_group(group_id),
    foreign key (user_id) references tb_user(user_id)
);

-- create table with group_vote_responses
CREATE TABLE tb_group_vote_responses (
	group_vote_response_id int auto_increment,
    group_vote_id int NOT NULL,
    group_id int NOT NULL,
    voter_id int NOT NULL,
    vote_response varchar(50) NOT NULL,
    primary key (group_vote_response_id),
    foreign key (group_vote_id) references tb_group_votes(group_vote_id),
    foreign key (group_id) references tb_group(group_id),
    foreign key (voter_id) references tb_user(user_id)
);

-- create report table where users, visitors, can report to SU for issues such with a user or group, etc
CREATE TABLE tb_reports (
	report_id int auto_increment,
    report_type varchar(50) NOT NULL, -- issues relating to users, a group
    reporter_id int NOT NULL,
    user_id int,
    group_id int,
    primary key (report_id),
    foreign key (reporter_id) references tb_user(user_id),
    foreign key (user_id) references tb_user(user_id),
    foreign key (group_id) references tb_group(group_id)
);

-- create appeals table where users can file for appeals to SU
CREATE TABLE tb_appeals (
	appeal_id int auto_increment,
    appealer_id int NOT NULL,
    appeal_type varchar(50) NOT NULL,
    appeal_decision varchar(50) NOT NULL default 'Pending',
    primary key (appeal_id),
    foreign key (appealer_id) references tb_user(user_id)
);

-- create compliment table system
CREATE TABLE tb_user_compliments (
	compliment_id int auto_increment,
    user_id int NOT NULL,
    complimentor_id int NOT NULL,
    primary key (compliment_id),
    foreign key (user_id) references tb_user(user_id),
    foreign key (complimentor_id) references tb_user(user_id)
);

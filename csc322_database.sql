DROP DATABASE IF EXISTS CSC322_PROJECT;
CREATE DATABASE CSC322_PROJECT;
use CSC322_PROJECT;

--  create table user
CREATE TABLE tb_user ( 
	user_id INT AUTO_INCREMENT,
    user_name VARCHAR(50) NOT NULL,
    user_password VARCHAR(50) NOT NULL ,
	email VARCHAR(100) NOT NULL ,
	PRIMARY KEY (user_id)
	);
 
-- setting user_id auto increment from 100
ALTER TABLE tb_user AUTO_INCREMENT = 100;

-- insert test data for user
insert into tb_user (user_name, user_password,  email) values 
('test1', '1', 'www.111@111.com'),
('test2','1','www.222@222.com'),
('test3','1', 'www.333@333.com'), 
('test4','1', 'www.444@444.com');

-- create table profile
create table tb_profile (
	user_id INT auto_increment,
    profile_display_name varchar (50),
    profile_user_type varchar (50),       -- 3 tpyes of users ordinary user, VIP, Super User 
    profile_user_scores INT default 0,    -- user scores  default 0
    profile_user_status bit default 1,    -- only 0 or 1;  1 means good standing, 0 means have been banned(into black list) 
    primary key (user_id)
    );

-- setting user_id auto increment from 100
ALTER TABLE tb_profile AUTO_INCREMENT = 100;

-- insert test data for profile
insert into tb_profile (profile_display_name, profile_user_type) values 
('AAA', 'OU'),
('BBB', 'OU'),
('CCC', 'VIP'),
('DDD', 'SU');

    
-- create table post
create table tb_post (
	post_id int auto_increment,
    post_job_id int,
    user_name varchar(50) not null,
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
    user_name varchar (50),
    reply_content text,
    reply_time timestamp default current_timestamp,
    primary key (reply_id),
    foreign key (user_id) references tb_user (user_id),
    foreign key (post_id) references tb_post (post_id)
	);
ALTER TABLE tb_reply AUTO_INCREMENT = 500;

-- create table team 
create table tb_team (
	team_id int auto_increment,
    team_name varchar(100) UNIQUE NOT NULL,
    team_content varchar(100) NOT NULL,
    primary key (team_id)
	);
-- team id start from 1000    
ALTER TABLE tb_team AUTO_INCREMENT = 1000;

-- insert test data for team
insert into tb_team (team_name, team_content) values 
('Blue', 'Blue Vikings FTW!'),
('Red', 'Red Spartans are the Champions'),
('Green', 'Green Leopards are Mighty!'), 
('Teal', 'Teal Tequila');

-- create group_member table
create table group_members (
	group_id int,
    user_id int,
    foreign key(group_id) references tb_team(team_id),
    foreign key(user_id) references tb_user(user_id)
); 

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
                INSERT INTO `group_members` VALUES(NEWGROUP, @value);
            ELSE
                INSERT INTO `group_members` VALUES(NEWGROUP, @value);
                -- to end while loop
                SET @myArrayOfUsers=  '';
            END IF;
            IF LENGTH(@myArrayOfUsers) > 0 AND LOCATE(',', @myArrayOfUsers) = 0 then
                -- Last entry was withóut comma
                INSERT INTO `group_members` VALUES(NEWGROUP, @myArrayOfUsers);
            END IF;
    END WHILE;
END$$

DELIMITER ;

CALL insert_members('101,103,102,100', 1001);
CALL insert_members('102,101', 1003);
CALL insert_members('103,101,102', 1000);
CALL insert_members('103,101,100', 1002);




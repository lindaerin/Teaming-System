DROP DATABASE IF EXISTS csc322_project;
CREATE DATABASE csc322_project;
use csc322_project;


-- create a table for all applications
CREATE TABLE tb_applied ( 
    username VARCHAR(50) NOT NULL,
	email VARCHAR(100) NOT NULL ,
    interest VARCHAR(50) NOT NULL,
    credential VARCHAR(50) NOT NULL,
    reference VARCHAR(50) NOT NULL,
    message text, 
	PRIMARY KEY (email)
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
('test2','1','www.222@222.com' .'0'),
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

-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Apr 22, 2025 at 09:42 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `blog`
--

-- --------------------------------------------------------

--
-- Table structure for table `admins`
--

CREATE TABLE `admins` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `admins`
--

INSERT INTO `admins` (`id`, `username`, `password`, `created_at`) VALUES
(1, 'admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', '2025-04-05 23:59:48');

-- --------------------------------------------------------

--
-- Table structure for table `comment_likes`
--

CREATE TABLE `comment_likes` (
  `id` int(11) NOT NULL,
  `comment_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `comment_reactions`
--

CREATE TABLE `comment_reactions` (
  `id` int(11) NOT NULL,
  `comment_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `featured_recipes`
--

CREATE TABLE `featured_recipes` (
  `id` int(11) NOT NULL,
  `recipe_id` int(11) NOT NULL,
  `featured_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `follows`
--

CREATE TABLE `follows` (
  `id` int(11) NOT NULL,
  `follower_id` int(11) NOT NULL,
  `followed_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `follows`
--

INSERT INTO `follows` (`id`, `follower_id`, `followed_id`, `created_at`) VALUES
(4, 6, 8, '2025-04-21 17:47:45'),
(5, 6, 7, '2025-04-21 17:47:50');

-- --------------------------------------------------------

--
-- Table structure for table `notifications`
--

CREATE TABLE `notifications` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `sender_id` int(11) DEFAULT NULL,
  `notification_type` varchar(50) NOT NULL,
  `entity_id` int(11) NOT NULL,
  `entity_type` varchar(50) NOT NULL,
  `is_read` tinyint(1) DEFAULT 0,
  `message` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `notifications`
--

INSERT INTO `notifications` (`id`, `user_id`, `sender_id`, `notification_type`, `entity_id`, `entity_type`, `is_read`, `message`, `created_at`) VALUES
(1, 6, 7, 'recipe_like', 25, 'recipe', 0, '<strong>Aleonah  Reese</strong> liked your recipe <strong>asda</strong>', '2025-04-22 03:41:47'),
(2, 8, 6, 'recipe_like', 22, 'recipe', 0, '<strong>Jezell Nadon</strong> liked your recipe <strong>Paella</strong>', '2025-04-22 07:37:34');

-- --------------------------------------------------------

--
-- Table structure for table `recipes`
--

CREATE TABLE `recipes` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `prep_time` int(11) DEFAULT NULL,
  `cook_time` int(11) DEFAULT NULL,
  `servings` int(11) DEFAULT NULL,
  `ingredients` text NOT NULL,
  `instructions` text NOT NULL,
  `photo_path` text DEFAULT NULL,
  `calories` int(11) DEFAULT NULL,
  `cuisine_type` enum('International','Luzon','Visayas','Mindanao','Other') DEFAULT 'Other',
  `privacy` varchar(20) NOT NULL DEFAULT 'public',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `likes_count` int(11) DEFAULT 0,
  `comments_count` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `recipes`
--

INSERT INTO `recipes` (`id`, `user_id`, `title`, `description`, `prep_time`, `cook_time`, `servings`, `ingredients`, `instructions`, `photo_path`, `calories`, `cuisine_type`, `privacy`, `created_at`, `updated_at`, `likes_count`, `comments_count`) VALUES
(8, 6, 'Kare Kare', 'It is generally made from a base of stewed oxtail, beef tripe, pork hocks, calves\' feet, pig\'s feet or trotters, various cuts of pork, beef stew meat, and occasionally offal.', 25, 90, 6, '2 lbs oxtail (or a mix of oxtail, beef tripe, and beef shank)\r\n,1 banana blossom (optional)\r\n,1 bundle string beans, cut into 2-inch pieces\r\n,1 eggplant, sliced diagonally\r\n,1 banana heart (optional), sliced\r\n,1 bundle pechay or bok choy\r\n,1/2 cup peanut butter (smooth or chunky, your choice)\r\n,1/4 cup ground toasted rice (or rice flour)\r\n,1/2 cup annatto seeds (soaked in 1/2 cup hot water) or 1 tsp annatto powder\r\n,1 medium onion, chopped\r\n,4 cloves garlic, minced\r\n,6 cups water (or beef broth)\r\n,Salt and pepper, to taste\r\n,Bagoong alamang (fermented shrimp paste), for serving', 'Boil the Meat\r\n,In a large pot, boil oxtail (and other meat, if using) in water until tender. This can take 1.5 to 2 hours, or 45 minutes in a pressure cooker. Skim off any scum.\r\n,\r\n,Prepare Annatto Oil\r\n,While meat cooks, soak annatto seeds in hot water for 10 minutes. Strain and discard seeds, keeping the red liquid. If using annatto powder, dissolve it in warm water.\r\n,\r\n,Sauté Aromatics\r\n,In a separate pan, heat some oil and sauté garlic and onion until translucent.\r\n,\r\n,Add Peanut Butter and Annatto Water\r\n,Stir in the peanut butter and annatto water. Mix until well combined and smooth.\r\n,\r\n,Thicken with Ground Rice\r\n,Add the ground toasted rice to the sauce. Stir well. It will start to thicken.\r\n,\r\n,Combine Meat and Sauce\r\n,Pour the sauce into the pot of cooked meat. Mix and simmer for another 10–15 minutes until flavors blend. Season with salt and pepper.\r\n,\r\n,Add Vegetables\r\n,Add eggplant and banana heart first, then string beans, and finally the pechay. Cook each for a few minutes until just tender.\r\n,\r\n,Serve\r\n,Serve hot with steamed rice and bagoong on the side.', 'uploads/recipe_photos/325f5e6ea68d4c26b41b4aec5bcd23c0_photo1696939990-1.jpeg', 650, 'Luzon', 'public', '2025-04-13 08:06:29', '2025-04-22 06:54:56', 1, 0),
(21, 7, 'Beef Bulgogi', 'Beef Bulgogi is a delicious Korean barbecue dish that consists of thinly sliced beef marinated in a flavorful mixture of soy sauce, sesame oil, garlic, and sugar. It’s typically cooked on a grill or in a pan and served with steamed rice and vegetables. The result is a juicy, tender, and aromatic beef dish that’s packed with flavor.', 30, 10, 4, '1 lb (450g) beef sirloin or rib-eye, thinly sliced against the grain\r\n,\r\n,3 tbsp soy sauce\r\n,\r\n,2 tbsp sesame oil\r\n,\r\n,1 tbsp brown sugar\r\n,\r\n,3 cloves garlic, minced\r\n,\r\n,1-inch piece of ginger, grated\r\n,\r\n,1 tbsp rice vinegar\r\n,\r\n,1 tbsp gochujang (Korean chili paste, optional for heat)\r\n,\r\n,1 tsp sesame seeds\r\n,\r\n,2 green onions, chopped (for garnish)\r\n,\r\n,1 tbsp vegetable oil (for cooking)\r\n,\r\n,1 small onion, thinly sliced\r\n,\r\n,1 carrot, julienned (optional)\r\n,\r\n,Cooked rice (for serving)\r\n,\r\n,Lettuce leaves (for serving, optional)', 'Marinate the beef:\r\n,\r\n,In a large bowl, mix together soy sauce, sesame oil, brown sugar, garlic, ginger, rice vinegar, and gochujang (if using). Stir until the sugar dissolves.\r\n,\r\n,Add the thinly sliced beef to the marinade, ensuring that the beef is fully coated. Cover and refrigerate for at least 30 minutes, or up to 2 hours for a deeper flavor.\r\n,\r\n,Cook the beef:\r\n,\r\n,Heat a large pan or skillet over medium-high heat and add the vegetable oil.\r\n,\r\n,Add the sliced onions and carrots (if using) to the pan and cook for about 2-3 minutes, until they begin to soften.\r\n,\r\n,Add the marinated beef to the pan, spreading it out evenly. Cook for about 5-7 minutes, stirring occasionally, until the beef is cooked through and slightly caramelized.\r\n,\r\n,Garnish and serve:\r\n,\r\n,Sprinkle sesame seeds and chopped green onions over the cooked beef for garnish.\r\n,\r\n,Serve the beef bulgogi with steamed rice and lettuce leaves (if using), where you can wrap the beef in the lettuce for a fresh, crunchy bite.', 'uploads/recipe_photos/ce5e69c0593a4092bed90a8ce4af0f57_istockphoto-1460479014-612x612.jpg', 400, 'International', 'public', '2025-04-20 18:06:56', '2025-04-22 06:55:45', 1, 0),
(22, 8, 'Paella', 'Paella is a traditional Spanish rice dish originally from the region of Valencia. It’s a one-pan meal, typically made with a variety of proteins like seafood, chicken, and rabbit, combined with aromatic spices such as saffron and paprika. Paella is famous for its vibrant color, rich flavors, and the delicious crispy rice at the bottom called “socarrat.”', 20, 45, 4, '2 tbsp olive oil\r\n,\r\n,1 onion, finely chopped\r\n,\r\n,1 red bell pepper, diced\r\n,\r\n,2 cloves garlic, minced\r\n,\r\n,1 ½ cups Arborio rice (or any short-grain rice)\r\n,\r\n,1 ½ tsp smoked paprika\r\n,\r\n,1 pinch saffron threads (or turmeric as a substitute)\r\n,\r\n,4 cups chicken or vegetable broth\r\n,\r\n,1 cup white wine (optional)\r\n,\r\n,1 ½ cups diced tomatoes (canned or fresh)\r\n,\r\n,1 cup peas (frozen or fresh)\r\n,\r\n,1 lb chicken thighs, boneless and skinless, cut into pieces\r\n,\r\n,½ lb shrimp, peeled and deveined\r\n,\r\n,½ lb mussels or clams, cleaned\r\n,\r\n,Lemon wedges, for serving\r\n,\r\n,Fresh parsley, chopped (for garnish)', 'Prepare the ingredients:\r\n,\r\n,Heat the olive oil in a large paella pan or wide skillet over medium heat. Add the chicken pieces and cook until browned, about 5-7 minutes. Remove and set aside.\r\n,\r\n,Cook the vegetables:\r\n,\r\n,In the same pan, add the onion, bell pepper, and garlic. Cook for about 3-4 minutes, until softened.\r\n,\r\n,Add spices and rice:\r\n,\r\n,Stir in the paprika, saffron, and rice. Cook for 1-2 minutes, allowing the rice to toast slightly and absorb the spices.\r\n,\r\n,Deglaze the pan:\r\n,\r\n,Add the white wine (if using) and let it cook off for about 2-3 minutes. Then add the diced tomatoes and broth. Stir everything together and bring to a simmer.\r\n,\r\n,Simmer the paella:\r\n,\r\n,Lower the heat and let the mixture simmer without stirring for about 20 minutes, or until the rice is almost tender and most of the liquid is absorbed.\r\n,\r\n,Add the seafood and peas:\r\n,\r\n,Arrange the shrimp, mussels, and peas on top of the rice. Cover the pan with a lid or foil and cook for another 5-7 minutes, or until the seafood is cooked through and the mussels have opened.\r\n,\r\n,Rest the paella:\r\n,\r\n,Remove the pan from the heat and let the paella rest, covered, for about 5 minutes. This helps the rice to finish cooking and develop the flavorful crispy layer on the bottom.\r\n,\r\n,Serve:\r\n,\r\n,Garnish with fresh parsley and lemon wedges. Serve hot and enjoy!', 'uploads/recipe_photos/ba81873201c3457b8dd31276ab5d8c1f_images.jpg', 600, 'International', 'public', '2025-04-20 18:11:27', '2025-04-22 07:37:37', 1, 0);

-- --------------------------------------------------------

--
-- Table structure for table `recipe_collections`
--

CREATE TABLE `recipe_collections` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `recipe_id` int(11) NOT NULL,
  `collection_name` varchar(100) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recipe_comments`
--

CREATE TABLE `recipe_comments` (
  `id` int(11) NOT NULL,
  `recipe_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `parent_comment_id` int(11) DEFAULT NULL,
  `comment_text` text NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `likes_count` int(11) DEFAULT 0,
  `reactions_count` int(11) DEFAULT 0,
  `replies_count` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recipe_likes`
--

CREATE TABLE `recipe_likes` (
  `id` int(11) NOT NULL,
  `recipe_id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `recipe_likes`
--

INSERT INTO `recipe_likes` (`id`, `recipe_id`, `user_id`, `created_at`) VALUES
(28, 8, 6, '2025-04-13 08:14:51'),
(31, 21, 7, '2025-04-20 18:08:26'),
(37, 22, 6, '2025-04-22 07:37:34');

-- --------------------------------------------------------

--
-- Table structure for table `recipe_photos`
--

CREATE TABLE `recipe_photos` (
  `id` int(11) NOT NULL,
  `recipe_id` int(11) NOT NULL,
  `photo_path` text NOT NULL,
  `caption` varchar(255) DEFAULT NULL,
  `is_primary` tinyint(1) DEFAULT 0,
  `upload_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `saved_recipes`
--

CREATE TABLE `saved_recipes` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `recipe_id` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `birthday` date DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `profile_pic` varchar(255) DEFAULT NULL,
  `display_name` varchar(100) DEFAULT NULL,
  `bio` text DEFAULT NULL,
  `location` varchar(100) DEFAULT NULL,
  `website` varchar(255) DEFAULT NULL,
  `profile_visibility` enum('public','followers','private') DEFAULT 'public',
  `comment_settings` enum('allowed','followers','disabled') DEFAULT 'allowed',
  `show_online_status` tinyint(1) DEFAULT 1,
  `show_activity_status` tinyint(1) DEFAULT 1,
  `allow_tagging` tinyint(1) DEFAULT 1,
  `email_comments` tinyint(1) DEFAULT 1,
  `email_likes` tinyint(1) DEFAULT 1,
  `email_followers` tinyint(1) DEFAULT 1,
  `email_messages` tinyint(1) DEFAULT 0,
  `email_newsletter` tinyint(1) DEFAULT 1,
  `push_comments` tinyint(1) DEFAULT 1,
  `push_likes` tinyint(1) DEFAULT 1,
  `push_followers` tinyint(1) DEFAULT 1,
  `push_messages` tinyint(1) DEFAULT 1,
  `is_suspended` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `first_name`, `last_name`, `email`, `phone`, `birthday`, `password`, `created_at`, `profile_pic`, `display_name`, `bio`, `location`, `website`, `profile_visibility`, `comment_settings`, `show_online_status`, `show_activity_status`, `allow_tagging`, `email_comments`, `email_likes`, `email_followers`, `email_messages`, `email_newsletter`, `push_comments`, `push_likes`, `push_followers`, `push_messages`, `is_suspended`) VALUES
(6, 'Jezell', 'Nadon', 'mike@gmail.com', '09123123321', '2025-04-24', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', '2025-04-06 07:01:18', 'uploads/profile_photos/user_6_1745293365_475023943_992811476026510_8124974231880712904_n.jpg', 'jezellnadon', 'Heeee', 'Banga, South Cotabato', NULL, 'public', 'allowed', 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0),
(7, 'Aleonah ', 'Reese', 'aleo@gmail.com', '09621237489', '2006-07-18', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', '2025-04-20 15:51:09', 'uploads/profile_photos/user_7_1745172035_profile-icon-design-free-vector.jpg', 'aleonah reese', NULL, NULL, NULL, 'public', 'allowed', 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0),
(8, 'Kyla', 'Ampo', 'kyla@gmail.com', '09123566127', '2004-12-08', '5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5', '2025-04-20 18:10:43', 'uploads/profile_photos/user_185b4eef7e1b42059391771c7ae68762_435540287_122099438030268755_3614648058411215687_n.jpg', 'kylaampo', NULL, NULL, NULL, 'public', 'allowed', 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admins`
--
ALTER TABLE `admins`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `comment_likes`
--
ALTER TABLE `comment_likes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_comment_like` (`comment_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `comment_reactions`
--
ALTER TABLE `comment_reactions`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_reaction` (`comment_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `featured_recipes`
--
ALTER TABLE `featured_recipes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_featured` (`recipe_id`);

--
-- Indexes for table `follows`
--
ALTER TABLE `follows`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_follow` (`follower_id`,`followed_id`),
  ADD KEY `followed_id` (`followed_id`);

--
-- Indexes for table `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `sender_id` (`sender_id`);

--
-- Indexes for table `recipes`
--
ALTER TABLE `recipes`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `recipe_collections`
--
ALTER TABLE `recipe_collections`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_collection` (`user_id`,`recipe_id`),
  ADD KEY `recipe_id` (`recipe_id`);

--
-- Indexes for table `recipe_comments`
--
ALTER TABLE `recipe_comments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `recipe_id` (`recipe_id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `parent_comment_id` (`parent_comment_id`);

--
-- Indexes for table `recipe_likes`
--
ALTER TABLE `recipe_likes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `recipe_id` (`recipe_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `recipe_photos`
--
ALTER TABLE `recipe_photos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `recipe_id` (`recipe_id`);

--
-- Indexes for table `saved_recipes`
--
ALTER TABLE `saved_recipes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_save` (`user_id`,`recipe_id`),
  ADD KEY `recipe_id` (`recipe_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admins`
--
ALTER TABLE `admins`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `comment_likes`
--
ALTER TABLE `comment_likes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `comment_reactions`
--
ALTER TABLE `comment_reactions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=18;

--
-- AUTO_INCREMENT for table `featured_recipes`
--
ALTER TABLE `featured_recipes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `follows`
--
ALTER TABLE `follows`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `recipes`
--
ALTER TABLE `recipes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- AUTO_INCREMENT for table `recipe_collections`
--
ALTER TABLE `recipe_collections`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `recipe_comments`
--
ALTER TABLE `recipe_comments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT for table `recipe_likes`
--
ALTER TABLE `recipe_likes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=38;

--
-- AUTO_INCREMENT for table `recipe_photos`
--
ALTER TABLE `recipe_photos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `saved_recipes`
--
ALTER TABLE `saved_recipes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `comment_likes`
--
ALTER TABLE `comment_likes`
  ADD CONSTRAINT `comment_likes_comment_fk` FOREIGN KEY (`comment_id`) REFERENCES `recipe_comments` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `comment_likes_user_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `comment_reactions`
--
ALTER TABLE `comment_reactions`
  ADD CONSTRAINT `comment_reactions_ibfk_1` FOREIGN KEY (`comment_id`) REFERENCES `recipe_comments` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `comment_reactions_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `featured_recipes`
--
ALTER TABLE `featured_recipes`
  ADD CONSTRAINT `featured_recipes_ibfk_1` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `follows`
--
ALTER TABLE `follows`
  ADD CONSTRAINT `follows_ibfk_1` FOREIGN KEY (`follower_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `follows_ibfk_2` FOREIGN KEY (`followed_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `notifications_ibfk_2` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `recipes`
--
ALTER TABLE `recipes`
  ADD CONSTRAINT `recipes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `recipe_collections`
--
ALTER TABLE `recipe_collections`
  ADD CONSTRAINT `recipe_collections_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `recipe_collections_ibfk_2` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `recipe_comments`
--
ALTER TABLE `recipe_comments`
  ADD CONSTRAINT `recipe_comments_parent_fk` FOREIGN KEY (`parent_comment_id`) REFERENCES `recipe_comments` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `recipe_comments_recipe_fk` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `recipe_comments_user_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `recipe_likes`
--
ALTER TABLE `recipe_likes`
  ADD CONSTRAINT `recipe_likes_ibfk_1` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `recipe_likes_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `recipe_photos`
--
ALTER TABLE `recipe_photos`
  ADD CONSTRAINT `recipe_photos_ibfk_1` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `saved_recipes`
--
ALTER TABLE `saved_recipes`
  ADD CONSTRAINT `saved_recipes_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `saved_recipes_ibfk_2` FOREIGN KEY (`recipe_id`) REFERENCES `recipes` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

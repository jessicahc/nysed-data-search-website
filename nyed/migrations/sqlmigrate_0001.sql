--
-- Create model BEDS_Mapping
--
CREATE TABLE `nyed_beds_mapping` (`beds_code` varchar(15) NOT NULL PRIMARY KEY, `name_desc` varchar(200) NOT NULL, `nrc_code` smallint NULL);
--
-- Create model Math_Result
--
CREATE TABLE `nyed_math_result` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `year` smallint NOT NULL, `grade` smallint NOT NULL, `total_tested` integer NOT NULL, `L1_count` integer NOT NULL, `L1_percent` smallint NOT NULL, `L2_count` integer NOT NULL, `L2_percent` smallint NOT NULL, `L3_count` integer NOT NULL, `L3_percent` smallint NOT NULL, `L4_count` integer NOT NULL, `L4_percent` smallint NOT NULL, `mean_score` smallint NULL, `beds_code_id` varchar(15) NOT NULL);
--
-- Create model ELA_Result
--
CREATE TABLE `nyed_ela_result` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `year` smallint NOT NULL, `grade` smallint NOT NULL, `total_tested` integer NOT NULL, `L1_count` integer NOT NULL, `L1_percent` smallint NOT NULL, `L2_count` integer NOT NULL, `L2_percent` smallint NOT NULL, `L3_count` integer NOT NULL, `L3_percent` smallint NOT NULL, `L4_count` integer NOT NULL, `L4_percent` smallint NOT NULL, `mean_score` smallint NULL, `beds_code_id` varchar(15) NOT NULL);
--
-- Create model Correlation_Data
--
CREATE TABLE `nyed_correlation_data` (`id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY, `year` smallint NOT NULL, `g1to6_class_size` smallint NOT NULL, `ela_g3to6_L1_percent` smallint NULL, `math_g3to6_L1_percent` smallint NULL, `per_free_lunch` smallint NULL, `per_reduced_lunch` smallint NULL, `beds_code_id` varchar(15) NOT NULL);
--
-- Create index nyed_math_r_beds_co_74fb44_idx on field(s) beds_code, year, grade of model math_result
--
CREATE INDEX `nyed_math_r_beds_co_74fb44_idx` ON `nyed_math_result` (`beds_code_id`, `year`, `grade`);
--
-- Create index nyed_ela_re_beds_co_c5705f_idx on field(s) beds_code, year, grade of model ela_result
--
CREATE INDEX `nyed_ela_re_beds_co_c5705f_idx` ON `nyed_ela_result` (`beds_code_id`, `year`, `grade`);
--
-- Create index nyed_correl_beds_co_26cf71_idx on field(s) beds_code, year of model correlation_data
--
CREATE INDEX `nyed_correl_beds_co_26cf71_idx` ON `nyed_correlation_data` (`beds_code_id`, `year`);
ALTER TABLE `nyed_math_result` ADD CONSTRAINT `nyed_math_result_beds_code_id_eaade56f_fk_nyed_beds` FOREIGN KEY (`beds_code_id`) REFERENCES `nyed_beds_mapping` (`beds_code`);
ALTER TABLE `nyed_ela_result` ADD CONSTRAINT `nyed_ela_result_beds_code_id_bb9a34ff_fk_nyed_beds` FOREIGN KEY (`beds_code_id`) REFERENCES `nyed_beds_mapping` (`beds_code`);
ALTER TABLE `nyed_correlation_data` ADD CONSTRAINT `nyed_correlation_dat_beds_code_id_8cbd5051_fk_nyed_beds` FOREIGN KEY (`beds_code_id`) REFERENCES `nyed_beds_mapping` (`beds_code`);

CREATE TABLE plant_conf(
    id int primary key,
    soil_moist int,
    led_bright int,
    led_hours int,
    led_dimming int,
    fans_cycle int,
    fans_runtime int,
    pump_runtime int,
    checkup_time int,
    p_id int,
    FOREIGN KEY (p_id) REFERENCES plants (id)   
);

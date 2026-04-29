CREATE TABLE STG_SALES_DAILY (
    opportunity_id VARCHAR(18) NOT NULL,
    amount DECIMAL(18, 2) NOT NULL,
    client_id INT NOT NULL,
    close_date DATE NOT NULL
);

CREATE PROCEDURE AutoRestockLowInventory()
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE productId INT;
    DECLARE currentStock INT;
    DECLARE reorderLevel INT;
    DECLARE reorderAmount INT DEFAULT 100;

    DECLARE cur CURSOR FOR
        SELECT ProductID, Stock, ReorderLevel
        FROM Products
        WHERE Stock < ReorderLevel;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO productId, currentStock, reorderLevel;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Insert reorder request
        INSERT INTO PurchaseOrders (ProductID, Quantity, OrderDate)
        VALUES (productId, reorderAmount, NOW());

        -- Optionally log action
        INSERT INTO InventoryLog (ProductID, Action, Quantity, Timestamp)
        VALUES (productId, 'Auto-Reorder', reorderAmount, NOW());
    END LOOP;

    CLOSE cur;
    COMMIT;
END;


CREATE PROCEDURE GenerateMonthlyInvoices(IN billingDate DATE)
BEGIN
    DECLARE cust_id INT;
    DECLARE total_purchase DECIMAL(10,2);
    DECLARE discount_rate DECIMAL(5,2);
    DECLARE invoice_amount DECIMAL(10,2);
    
    DECLARE done INT DEFAULT FALSE;
    DECLARE cur CURSOR FOR
        SELECT CustomerID, SUM(TotalAmount)
        FROM Orders
        WHERE MONTH(OrderDate) = MONTH(billingDate)
          AND YEAR(OrderDate) = YEAR(billingDate)
        GROUP BY CustomerID;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION;

    OPEN cur;

    read_loop: LOOP
        FETCH cur INTO cust_id, total_purchase;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Determine discount
        IF total_purchase > 1000 THEN
            SET discount_rate = 0.10;
        ELSEIF total_purchase > 500 THEN
            SET discount_rate = 0.05;
        ELSE
            SET discount_rate = 0.00;
        END IF;

        SET invoice_amount = total_purchase * (1 - discount_rate);

        -- Insert invoice
        INSERT INTO Invoices (CustomerID, InvoiceDate, TotalAmount, DiscountApplied)
        VALUES (cust_id, billingDate, invoice_amount, discount_rate);
    END LOOP;

    CLOSE cur;
    COMMIT;
END;

CREATE PROCEDURE ArchiveOldOrders(IN archiveBefore DATE)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Error archiving old orders';
    END;

    START TRANSACTION;

    -- Move to archive
    INSERT INTO OrdersArchive
    SELECT * FROM Orders
    WHERE OrderDate < archiveBefore;

    -- Delete from live table
    DELETE FROM Orders
    WHERE OrderDate < archiveBefore;

    COMMIT;
END;

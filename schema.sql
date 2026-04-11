-- ============================================================
-- ASK Academy School Management System
-- Clean Database Schema for Azure SQL
-- Run this ONCE on a fresh ASK_Academy database
-- ============================================================

USE ASK_Academy;
GO

-- ── Core lookup tables ──────────────────────────────────────

CREATE TABLE dbo.Class (
    ClassID VARCHAR(10) PRIMARY KEY
        CHECK (ClassID IN ('MAT9','MAT10','INT1','INT2')),
    Name    VARCHAR(50) NOT NULL
);
GO

CREATE TABLE dbo.Batch (
    BatchID VARCHAR(10) PRIMARY KEY,
    Name    VARCHAR(50) NOT NULL,
    Year    INT         NOT NULL,
    Program VARCHAR(20) NOT NULL CHECK (Program IN ('Matric','Intermediate')),
    ClassID VARCHAR(10) NOT NULL,
    CONSTRAINT CHK_BatchClass CHECK (
        (Program = 'Matric'       AND ClassID IN ('MAT9','MAT10')) OR
        (Program = 'Intermediate' AND ClassID IN ('INT1','INT2'))
    )
);
GO

CREATE TABLE dbo.Room (
    RoomID      VARCHAR(10) PRIMARY KEY,
    Capacity    INT         NOT NULL CHECK (Capacity IN (40,60,80)),
    AC_Count    INT         NOT NULL DEFAULT 0,
    Chair_Count INT         NOT NULL DEFAULT 0,
    ClassID     VARCHAR(10) NOT NULL REFERENCES dbo.Class(ClassID)
);
GO

-- ── People ──────────────────────────────────────────────────

CREATE TABLE dbo.Student (
    StudentID       VARCHAR(15) PRIMARY KEY,
    Name            VARCHAR(100) NOT NULL,
    Contact         VARCHAR(15),
    ParentContact   VARCHAR(15)  NOT NULL,
    YearOfAdmission INT          NOT NULL,
    BatchID         VARCHAR(10)  NOT NULL REFERENCES dbo.Batch(BatchID),
    ClassID         VARCHAR(10)  NOT NULL REFERENCES dbo.Class(ClassID)
);
GO

CREATE TABLE dbo.Teacher (
    TeacherID   VARCHAR(10)    PRIMARY KEY,
    Name        VARCHAR(100)   NOT NULL,
    Subject     VARCHAR(50)    NOT NULL,
    DailySalary DECIMAL(10,2)  NOT NULL CHECK (DailySalary > 0)
);
GO

CREATE TABLE dbo.Users (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(50) NOT NULL,
    role     VARCHAR(10) NOT NULL CHECK (role IN ('owner','staff'))
);
GO

-- ── Academic ────────────────────────────────────────────────

CREATE TABLE dbo.TimetableEntry (
    BatchID VARCHAR(10)  NOT NULL REFERENCES dbo.Batch(BatchID),
    Day     VARCHAR(10)  NOT NULL CHECK (Day IN ('Monday','Tuesday','Wednesday','Thursday','Friday')),
    Period  INT          NOT NULL CHECK (Period BETWEEN 1 AND 6),
    Subject VARCHAR(50)  NOT NULL,
    PRIMARY KEY (BatchID, Day, Period)
);
GO

CREATE TABLE dbo.Test (
    TestID   VARCHAR(10) PRIMARY KEY,
    Subject  VARCHAR(50) NOT NULL,
    Date     DATE        NOT NULL,
    MaxMarks INT         NOT NULL CHECK (MaxMarks > 0),
    BatchID  VARCHAR(10) NOT NULL REFERENCES dbo.Batch(BatchID),
    ClassID  VARCHAR(10) NOT NULL REFERENCES dbo.Class(ClassID)
);
GO

CREATE TABLE dbo.Result (
    ResultID      VARCHAR(10)   PRIMARY KEY,
    StudentID     VARCHAR(15)   NOT NULL REFERENCES dbo.Student(StudentID),
    TestID        VARCHAR(10)   NOT NULL REFERENCES dbo.Test(TestID),
    ObtainedMarks DECIMAL(10,2) NOT NULL CHECK (ObtainedMarks >= 0)
);
GO

-- ── Attendance ──────────────────────────────────────────────

CREATE TABLE dbo.Attendance (
    AttendanceID VARCHAR(10) PRIMARY KEY,
    StudentID    VARCHAR(15) NOT NULL REFERENCES dbo.Student(StudentID),
    Date         DATE        NOT NULL,
    Status       VARCHAR(10) NOT NULL CHECK (Status IN ('Present','Absent'))
);
GO

CREATE TABLE dbo.TeacherAttendance (
    AttendanceID VARCHAR(10) PRIMARY KEY,
    TeacherID    VARCHAR(10) NOT NULL REFERENCES dbo.Teacher(TeacherID),
    Date         DATE        NOT NULL,
    Status       VARCHAR(10) NOT NULL CHECK (Status IN ('Present','Absent'))
);
GO

-- ── Finance ─────────────────────────────────────────────────

CREATE TABLE dbo.Salary (
    SalaryID        VARCHAR(10)   PRIMARY KEY,
    TeacherID       VARCHAR(10)   NOT NULL REFERENCES dbo.Teacher(TeacherID),
    Month           VARCHAR(7)    NOT NULL,   -- YYYY-MM
    TotalDaysPresent INT          NOT NULL DEFAULT 0,
    Amount          DECIMAL(10,2) NOT NULL DEFAULT 0
);
GO

CREATE TABLE dbo.Fee (
    FeeID      VARCHAR(10)   PRIMARY KEY,
    StudentID  VARCHAR(15)   NOT NULL REFERENCES dbo.Student(StudentID),
    Amount     DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Discount   DECIMAL(10,2) DEFAULT 0,
    DueDate    DATE          NOT NULL,
    PaidStatus BIT           NOT NULL DEFAULT 0
);
GO

CREATE TABLE dbo.Expense (
    ExpenseID VARCHAR(10)   PRIMARY KEY,
    Type      VARCHAR(50)   NOT NULL,
    Amount    DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Date      DATE          NOT NULL
);
GO

-- ── Assets ──────────────────────────────────────────────────

CREATE TABLE dbo.ClassroomAsset (
    AssetID  VARCHAR(10) PRIMARY KEY,
    RoomID   VARCHAR(10) NOT NULL REFERENCES dbo.Room(RoomID),
    Type     VARCHAR(20) NOT NULL CHECK (Type IN ('Chair','AC')),
    Quantity INT         NOT NULL CHECK (Quantity >= 0)
);
GO

CREATE TABLE dbo.Maintenance (
    MaintenanceID VARCHAR(10)   PRIMARY KEY,
    AssetID       VARCHAR(10)   NOT NULL REFERENCES dbo.ClassroomAsset(AssetID),
    RepairDate    DATE          NOT NULL,
    Cost          DECIMAL(10,2) NOT NULL CHECK (Cost >= 0),
    Status        VARCHAR(10)   NOT NULL CHECK (Status IN ('Pending','Done'))
);
GO

-- ── Audit log ───────────────────────────────────────────────

CREATE TABLE dbo.AuditLog (
    LogID      INT IDENTITY(1,1) PRIMARY KEY,
    TableName  VARCHAR(50),
    Action     VARCHAR(10),
    RecordID   VARCHAR(50),
    ChangedBy  VARCHAR(100),
    ChangeDate DATETIME DEFAULT GETDATE(),
    OldValues  NVARCHAR(MAX),
    NewValues  NVARCHAR(MAX)
);
GO

-- ── Stored Procedures ────────────────────────────────────────

CREATE PROCEDURE dbo.sp_InsertStudent
    @StudentID VARCHAR(15), @Name VARCHAR(100),
    @Contact VARCHAR(15), @ParentContact VARCHAR(15),
    @YearOfAdmission INT, @BatchID VARCHAR(10), @ClassID VARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;
    IF @YearOfAdmission < 2000 OR @YearOfAdmission > YEAR(GETDATE())
        THROW 50001, 'YearOfAdmission must be between 2000 and current year.', 1;
    IF NOT EXISTS (SELECT 1 FROM dbo.Batch WHERE BatchID = @BatchID)
        THROW 50002, 'Invalid BatchID.', 1;
    IF NOT EXISTS (SELECT 1 FROM dbo.Class WHERE ClassID = @ClassID)
        THROW 50003, 'Invalid ClassID.', 1;
    INSERT INTO dbo.Student VALUES (@StudentID,@Name,@Contact,@ParentContact,@YearOfAdmission,@BatchID,@ClassID);
END;
GO

CREATE PROCEDURE dbo.sp_UpdateStudent
    @StudentID VARCHAR(15), @Name VARCHAR(100),
    @Contact VARCHAR(15), @ParentContact VARCHAR(15),
    @YearOfAdmission INT, @BatchID VARCHAR(10), @ClassID VARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.Student WHERE StudentID = @StudentID)
        THROW 50010, 'Student not found.', 1;
    UPDATE dbo.Student
    SET Name=@Name, Contact=@Contact, ParentContact=@ParentContact,
        YearOfAdmission=@YearOfAdmission, BatchID=@BatchID, ClassID=@ClassID
    WHERE StudentID = @StudentID;
END;
GO

CREATE PROCEDURE dbo.sp_InsertTimetableEntry
    @BatchID VARCHAR(10), @Day VARCHAR(10), @Period INT, @Subject VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.Batch WHERE BatchID = @BatchID)
        THROW 50020, 'Invalid BatchID.', 1;
    IF EXISTS (SELECT 1 FROM dbo.TimetableEntry WHERE BatchID=@BatchID AND Day=@Day AND Period=@Period)
        THROW 50021, 'A timetable entry already exists for this slot.', 1;
    INSERT INTO dbo.TimetableEntry VALUES (@BatchID,@Day,@Period,@Subject);
END;
GO

CREATE PROCEDURE dbo.sp_InsertClassroomAsset
    @RoomID VARCHAR(10), @Type VARCHAR(20), @Quantity INT
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.Room WHERE RoomID = @RoomID)
        THROW 50030, 'Invalid RoomID.', 1;
    DECLARE @NextID INT = ISNULL((SELECT MAX(TRY_CAST(SUBSTRING(AssetID,6,10) AS INT)) FROM dbo.ClassroomAsset),0)+1;
    DECLARE @AssetID VARCHAR(10) = 'ASSET' + RIGHT('000'+CAST(@NextID AS VARCHAR),3);
    INSERT INTO dbo.ClassroomAsset VALUES (@AssetID,@RoomID,@Type,@Quantity);
END;
GO

-- ── Triggers ────────────────────────────────────────────────

-- Auto-audit on Student
CREATE TRIGGER dbo.TR_Student_Audit ON dbo.Student AFTER INSERT,UPDATE,DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Action VARCHAR(10) = CASE
        WHEN EXISTS(SELECT 1 FROM INSERTED) AND EXISTS(SELECT 1 FROM DELETED) THEN 'UPDATE'
        WHEN EXISTS(SELECT 1 FROM INSERTED) THEN 'INSERT' ELSE 'DELETE' END;
    INSERT INTO dbo.AuditLog(TableName,Action,RecordID,ChangedBy,OldValues,NewValues)
    SELECT 'Student',@Action,COALESCE(i.StudentID,d.StudentID),SUSER_SNAME(),
           (SELECT * FROM DELETED  FOR JSON PATH),
           (SELECT * FROM INSERTED FOR JSON PATH)
    FROM INSERTED i FULL OUTER JOIN DELETED d ON i.StudentID=d.StudentID;
END;
GO

-- Auto-audit on Teacher
CREATE TRIGGER dbo.TR_Teacher_Audit ON dbo.Teacher AFTER INSERT,UPDATE,DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Action VARCHAR(10) = CASE
        WHEN EXISTS(SELECT 1 FROM INSERTED) AND EXISTS(SELECT 1 FROM DELETED) THEN 'UPDATE'
        WHEN EXISTS(SELECT 1 FROM INSERTED) THEN 'INSERT' ELSE 'DELETE' END;
    INSERT INTO dbo.AuditLog(TableName,Action,RecordID,ChangedBy,OldValues,NewValues)
    SELECT 'Teacher',@Action,COALESCE(i.TeacherID,d.TeacherID),SUSER_SNAME(),
           (SELECT * FROM DELETED  FOR JSON PATH),
           (SELECT * FROM INSERTED FOR JSON PATH)
    FROM INSERTED i FULL OUTER JOIN DELETED d ON i.TeacherID=d.TeacherID;
END;
GO

-- Validate obtained marks never exceed max marks
CREATE TRIGGER dbo.TR_ValidateResultMarks ON dbo.Result AFTER INSERT,UPDATE
AS
BEGIN
    IF EXISTS (
        SELECT 1 FROM INSERTED i JOIN dbo.Test t ON i.TestID=t.TestID
        WHERE i.ObtainedMarks > t.MaxMarks)
    BEGIN
        THROW 50040, 'Obtained marks cannot exceed the test maximum marks.', 1;
        ROLLBACK;
    END
END;
GO

-- Prevent attendance dates in the future
CREATE TRIGGER dbo.TR_PreventFutureAttendance ON dbo.Attendance AFTER INSERT,UPDATE
AS
BEGIN
    IF EXISTS (SELECT 1 FROM INSERTED WHERE Date > CAST(GETDATE() AS DATE))
    BEGIN
        THROW 50050, 'Attendance date cannot be in the future.', 1;
        ROLLBACK;
    END
END;
GO

-- Prevent batch deletion when students are enrolled
CREATE TRIGGER dbo.TR_PreventBatchDeletion ON dbo.Batch INSTEAD OF DELETE
AS
BEGIN
    IF EXISTS (SELECT 1 FROM DELETED d JOIN dbo.Student s ON d.BatchID=s.BatchID)
    BEGIN
        THROW 50060, 'Cannot delete a batch that has enrolled students.', 1;
        ROLLBACK;
    END
    ELSE
        DELETE FROM dbo.Batch WHERE BatchID IN (SELECT BatchID FROM DELETED);
END;
GO

-- ── Default users ────────────────────────────────────────────

INSERT INTO dbo.Users VALUES ('admin',  'admin123',  'owner');
INSERT INTO dbo.Users VALUES ('staff1', 'staff123',  'staff');
GO

"""
ASK Academy – Schema + Sample Data Seeder
==========================================
1. Creates all tables, stored procedures, and triggers (safe to run on a
   fresh database – skips objects that already exist).
2. Inserts representative sample rows into every table in FK-safe order.

Usage:
    pip install pyodbc
    python seed_data.py
"""

import pyodbc
from datetime import date, timedelta

# ── Connection ────────────────────────────────────────────────────────────────
CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=tcp:ask-academy1.database.windows.net,1433;"
    "DATABASE=ASK_Academy;"
    "UID=sufyan;"
    "PWD=sufysufysufy0!;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)

# ── Full schema (each string = one GO batch) ──────────────────────────────────
# Wrapped in IF NOT EXISTS so re-running is always safe.

SCHEMA_BATCHES = [
    # ── Tables ────────────────────────────────────────────────────────────────
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Class' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Class (
    ClassID VARCHAR(10) PRIMARY KEY
        CHECK (ClassID IN ('MAT9','MAT10','INT1','INT2')),
    Name    VARCHAR(50) NOT NULL
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Batch' AND schema_id=SCHEMA_ID('dbo'))
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
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Room' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Room (
    RoomID      VARCHAR(10) PRIMARY KEY,
    Capacity    INT         NOT NULL CHECK (Capacity IN (40,60,80)),
    AC_Count    INT         NOT NULL DEFAULT 0,
    Chair_Count INT         NOT NULL DEFAULT 0,
    ClassID     VARCHAR(10) NOT NULL REFERENCES dbo.Class(ClassID)
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Student' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Student (
    StudentID       VARCHAR(15)  PRIMARY KEY,
    Name            VARCHAR(100) NOT NULL,
    Contact         VARCHAR(15),
    ParentContact   VARCHAR(15)  NOT NULL,
    YearOfAdmission INT          NOT NULL,
    BatchID         VARCHAR(10)  NOT NULL REFERENCES dbo.Batch(BatchID),
    ClassID         VARCHAR(10)  NOT NULL REFERENCES dbo.Class(ClassID)
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Teacher' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Teacher (
    TeacherID   VARCHAR(10)   PRIMARY KEY,
    Name        VARCHAR(100)  NOT NULL,
    Subject     VARCHAR(50)   NOT NULL,
    DailySalary DECIMAL(10,2) NOT NULL CHECK (DailySalary > 0)
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Users' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Users (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(50) NOT NULL,
    role     VARCHAR(10) NOT NULL CHECK (role IN ('owner','staff'))
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='TimetableEntry' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.TimetableEntry (
    BatchID VARCHAR(10) NOT NULL REFERENCES dbo.Batch(BatchID),
    Day     VARCHAR(10) NOT NULL CHECK (Day IN ('Monday','Tuesday','Wednesday','Thursday','Friday')),
    Period  INT         NOT NULL CHECK (Period BETWEEN 1 AND 6),
    Subject VARCHAR(50) NOT NULL,
    PRIMARY KEY (BatchID, Day, Period)
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Test' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Test (
    TestID   VARCHAR(10) PRIMARY KEY,
    Subject  VARCHAR(50) NOT NULL,
    Date     DATE        NOT NULL,
    MaxMarks INT         NOT NULL CHECK (MaxMarks > 0),
    BatchID  VARCHAR(10) NOT NULL REFERENCES dbo.Batch(BatchID),
    ClassID  VARCHAR(10) NOT NULL REFERENCES dbo.Class(ClassID)
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Result' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Result (
    ResultID      VARCHAR(10)   PRIMARY KEY,
    StudentID     VARCHAR(15)   NOT NULL REFERENCES dbo.Student(StudentID),
    TestID        VARCHAR(10)   NOT NULL REFERENCES dbo.Test(TestID),
    ObtainedMarks DECIMAL(10,2) NOT NULL CHECK (ObtainedMarks >= 0)
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Attendance' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Attendance (
    AttendanceID VARCHAR(10) PRIMARY KEY,
    StudentID    VARCHAR(15) NOT NULL REFERENCES dbo.Student(StudentID),
    Date         DATE        NOT NULL,
    Status       VARCHAR(10) NOT NULL CHECK (Status IN ('Present','Absent'))
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='TeacherAttendance' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.TeacherAttendance (
    AttendanceID VARCHAR(10) PRIMARY KEY,
    TeacherID    VARCHAR(10) NOT NULL REFERENCES dbo.Teacher(TeacherID),
    Date         DATE        NOT NULL,
    Status       VARCHAR(10) NOT NULL CHECK (Status IN ('Present','Absent'))
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Salary' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Salary (
    SalaryID         VARCHAR(10)   PRIMARY KEY,
    TeacherID        VARCHAR(10)   NOT NULL REFERENCES dbo.Teacher(TeacherID),
    Month            VARCHAR(7)    NOT NULL,
    TotalDaysPresent INT           NOT NULL DEFAULT 0,
    Amount           DECIMAL(10,2) NOT NULL DEFAULT 0
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Fee' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Fee (
    FeeID      VARCHAR(10)   PRIMARY KEY,
    StudentID  VARCHAR(15)   NOT NULL REFERENCES dbo.Student(StudentID),
    Amount     DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Discount   DECIMAL(10,2) DEFAULT 0,
    DueDate    DATE          NOT NULL,
    PaidStatus BIT           NOT NULL DEFAULT 0
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Expense' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Expense (
    ExpenseID VARCHAR(10)   PRIMARY KEY,
    Type      VARCHAR(50)   NOT NULL,
    Amount    DECIMAL(10,2) NOT NULL CHECK (Amount >= 0),
    Date      DATE          NOT NULL
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='ClassroomAsset' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.ClassroomAsset (
    AssetID  VARCHAR(10) PRIMARY KEY,
    RoomID   VARCHAR(10) NOT NULL REFERENCES dbo.Room(RoomID),
    Type     VARCHAR(20) NOT NULL CHECK (Type IN ('Chair','AC')),
    Quantity INT         NOT NULL CHECK (Quantity >= 0)
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='Maintenance' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.Maintenance (
    MaintenanceID VARCHAR(10)   PRIMARY KEY,
    AssetID       VARCHAR(10)   NOT NULL REFERENCES dbo.ClassroomAsset(AssetID),
    RepairDate    DATE          NOT NULL,
    Cost          DECIMAL(10,2) NOT NULL CHECK (Cost >= 0),
    Status        VARCHAR(10)   NOT NULL CHECK (Status IN ('Pending','Done'))
)
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='AuditLog' AND schema_id=SCHEMA_ID('dbo'))
CREATE TABLE dbo.AuditLog (
    LogID      INT IDENTITY(1,1) PRIMARY KEY,
    TableName  VARCHAR(50),
    Action     VARCHAR(10),
    RecordID   VARCHAR(50),
    ChangedBy  VARCHAR(100),
    ChangeDate DATETIME DEFAULT GETDATE(),
    OldValues  NVARCHAR(MAX),
    NewValues  NVARCHAR(MAX)
)
""",
    # ── Stored Procedures ─────────────────────────────────────────────────────
    """
IF NOT EXISTS (SELECT 1 FROM sys.procedures WHERE name='sp_InsertStudent' AND schema_id=SCHEMA_ID('dbo'))
EXEC('
CREATE PROCEDURE dbo.sp_InsertStudent
    @StudentID VARCHAR(15), @Name VARCHAR(100),
    @Contact VARCHAR(15), @ParentContact VARCHAR(15),
    @YearOfAdmission INT, @BatchID VARCHAR(10), @ClassID VARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;
    IF @YearOfAdmission < 2000 OR @YearOfAdmission > YEAR(GETDATE())
        THROW 50001, ''YearOfAdmission must be between 2000 and current year.'', 1;
    IF NOT EXISTS (SELECT 1 FROM dbo.Batch WHERE BatchID = @BatchID)
        THROW 50002, ''Invalid BatchID.'', 1;
    IF NOT EXISTS (SELECT 1 FROM dbo.Class WHERE ClassID = @ClassID)
        THROW 50003, ''Invalid ClassID.'', 1;
    INSERT INTO dbo.Student VALUES (@StudentID,@Name,@Contact,@ParentContact,@YearOfAdmission,@BatchID,@ClassID);
END
')
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.procedures WHERE name='sp_UpdateStudent' AND schema_id=SCHEMA_ID('dbo'))
EXEC('
CREATE PROCEDURE dbo.sp_UpdateStudent
    @StudentID VARCHAR(15), @Name VARCHAR(100),
    @Contact VARCHAR(15), @ParentContact VARCHAR(15),
    @YearOfAdmission INT, @BatchID VARCHAR(10), @ClassID VARCHAR(10)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.Student WHERE StudentID = @StudentID)
        THROW 50010, ''Student not found.'', 1;
    UPDATE dbo.Student
    SET Name=@Name, Contact=@Contact, ParentContact=@ParentContact,
        YearOfAdmission=@YearOfAdmission, BatchID=@BatchID, ClassID=@ClassID
    WHERE StudentID = @StudentID;
END
')
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.procedures WHERE name='sp_InsertTimetableEntry' AND schema_id=SCHEMA_ID('dbo'))
EXEC('
CREATE PROCEDURE dbo.sp_InsertTimetableEntry
    @BatchID VARCHAR(10), @Day VARCHAR(10), @Period INT, @Subject VARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.Batch WHERE BatchID = @BatchID)
        THROW 50020, ''Invalid BatchID.'', 1;
    IF EXISTS (SELECT 1 FROM dbo.TimetableEntry WHERE BatchID=@BatchID AND Day=@Day AND Period=@Period)
        THROW 50021, ''A timetable entry already exists for this slot.'', 1;
    INSERT INTO dbo.TimetableEntry VALUES (@BatchID,@Day,@Period,@Subject);
END
')
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.procedures WHERE name='sp_InsertClassroomAsset' AND schema_id=SCHEMA_ID('dbo'))
EXEC('
CREATE PROCEDURE dbo.sp_InsertClassroomAsset
    @RoomID VARCHAR(10), @Type VARCHAR(20), @Quantity INT
AS
BEGIN
    SET NOCOUNT ON;
    IF NOT EXISTS (SELECT 1 FROM dbo.Room WHERE RoomID = @RoomID)
        THROW 50030, ''Invalid RoomID.'', 1;
    DECLARE @NextID INT = ISNULL((SELECT MAX(TRY_CAST(SUBSTRING(AssetID,6,10) AS INT)) FROM dbo.ClassroomAsset),0)+1;
    DECLARE @AssetID VARCHAR(10) = ''ASSET'' + RIGHT(''000''+CAST(@NextID AS VARCHAR),3);
    INSERT INTO dbo.ClassroomAsset VALUES (@AssetID,@RoomID,@Type,@Quantity);
END
')
""",
    # ── Triggers ─────────────────────────────────────────────────────────────
    """
IF NOT EXISTS (SELECT 1 FROM sys.triggers WHERE name='TR_Student_Audit')
EXEC('
CREATE TRIGGER dbo.TR_Student_Audit ON dbo.Student AFTER INSERT,UPDATE,DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Action VARCHAR(10) = CASE
        WHEN EXISTS(SELECT 1 FROM INSERTED) AND EXISTS(SELECT 1 FROM DELETED) THEN ''UPDATE''
        WHEN EXISTS(SELECT 1 FROM INSERTED) THEN ''INSERT'' ELSE ''DELETE'' END;
    INSERT INTO dbo.AuditLog(TableName,Action,RecordID,ChangedBy,OldValues,NewValues)
    SELECT ''Student'',@Action,COALESCE(i.StudentID,d.StudentID),SUSER_SNAME(),
           (SELECT * FROM DELETED  FOR JSON PATH),
           (SELECT * FROM INSERTED FOR JSON PATH)
    FROM INSERTED i FULL OUTER JOIN DELETED d ON i.StudentID=d.StudentID;
END
')
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.triggers WHERE name='TR_Teacher_Audit')
EXEC('
CREATE TRIGGER dbo.TR_Teacher_Audit ON dbo.Teacher AFTER INSERT,UPDATE,DELETE
AS
BEGIN
    SET NOCOUNT ON;
    DECLARE @Action VARCHAR(10) = CASE
        WHEN EXISTS(SELECT 1 FROM INSERTED) AND EXISTS(SELECT 1 FROM DELETED) THEN ''UPDATE''
        WHEN EXISTS(SELECT 1 FROM INSERTED) THEN ''INSERT'' ELSE ''DELETE'' END;
    INSERT INTO dbo.AuditLog(TableName,Action,RecordID,ChangedBy,OldValues,NewValues)
    SELECT ''Teacher'',@Action,COALESCE(i.TeacherID,d.TeacherID),SUSER_SNAME(),
           (SELECT * FROM DELETED  FOR JSON PATH),
           (SELECT * FROM INSERTED FOR JSON PATH)
    FROM INSERTED i FULL OUTER JOIN DELETED d ON i.TeacherID=d.TeacherID;
END
')
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.triggers WHERE name='TR_ValidateResultMarks')
EXEC('
CREATE TRIGGER dbo.TR_ValidateResultMarks ON dbo.Result AFTER INSERT,UPDATE
AS
BEGIN
    IF EXISTS (
        SELECT 1 FROM INSERTED i JOIN dbo.Test t ON i.TestID=t.TestID
        WHERE i.ObtainedMarks > t.MaxMarks)
    BEGIN
        THROW 50040, ''Obtained marks cannot exceed the test maximum marks.'', 1;
        ROLLBACK;
    END
END
')
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.triggers WHERE name='TR_PreventFutureAttendance')
EXEC('
CREATE TRIGGER dbo.TR_PreventFutureAttendance ON dbo.Attendance AFTER INSERT,UPDATE
AS
BEGIN
    IF EXISTS (SELECT 1 FROM INSERTED WHERE Date > CAST(GETDATE() AS DATE))
    BEGIN
        THROW 50050, ''Attendance date cannot be in the future.'', 1;
        ROLLBACK;
    END
END
')
""",
    """
IF NOT EXISTS (SELECT 1 FROM sys.triggers WHERE name='TR_PreventBatchDeletion')
EXEC('
CREATE TRIGGER dbo.TR_PreventBatchDeletion ON dbo.Batch INSTEAD OF DELETE
AS
BEGIN
    IF EXISTS (SELECT 1 FROM DELETED d JOIN dbo.Student s ON d.BatchID=s.BatchID)
    BEGIN
        THROW 50060, ''Cannot delete a batch that has enrolled students.'', 1;
        ROLLBACK;
    END
    ELSE
        DELETE FROM dbo.Batch WHERE BatchID IN (SELECT BatchID FROM DELETED);
END
')
""",
    # ── Default users ─────────────────────────────────────────────────────────
    """
IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE username='admin')
    INSERT INTO dbo.Users VALUES ('admin', 'admin123', 'owner')
""",
    """
IF NOT EXISTS (SELECT 1 FROM dbo.Users WHERE username='staff1')
    INSERT INTO dbo.Users VALUES ('staff1', 'staff123', 'staff')
""",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def exists(cur, table, pk_col, pk_val):
    cur.execute(f"SELECT 1 FROM dbo.{table} WHERE {pk_col} = ?", pk_val)
    return cur.fetchone() is not None


def insert_if_new(cur, table, pk_col, pk_val, columns, values):
    if not exists(cur, table, pk_col, pk_val):
        placeholders = ", ".join(["?"] * len(values))
        col_list = ", ".join(columns)
        cur.execute(
            f"INSERT INTO dbo.{table} ({col_list}) VALUES ({placeholders})",
            values,
        )
        return True
    return False


def log(msg):
    print(f"  {msg}")


# ── Schema runner ─────────────────────────────────────────────────────────────

def run_schema(conn):
    print("\n── Creating schema objects (skipping any that already exist) ──")
    cur = conn.cursor()
    for batch in SCHEMA_BATCHES:
        sql = batch.strip()
        if not sql:
            continue
        try:
            cur.execute(sql)
            conn.commit()
        except pyodbc.Error as e:
            print(f"  [WARN] {e}")
    cur.close()
    print("  Schema ready.\n")


# ── Seed functions ────────────────────────────────────────────────────────────

def seed_classes(cur):
    rows = [
        ("MAT9",  "Matric - 9th Grade"),
        ("MAT10", "Matric - 10th Grade"),
        ("INT1",  "Intermediate - 1st Year"),
        ("INT2",  "Intermediate - 2nd Year"),
    ]
    for cid, name in rows:
        ok = insert_if_new(cur, "Class", "ClassID", cid,
                           ["ClassID", "Name"], [cid, name])
        log(f"Class {cid}: {'inserted' if ok else 'already exists'}")


def seed_batches(cur):
    rows = [
        ("B-M9-25",  "Matric 9th 2025",  2025, "Matric",       "MAT9"),
        ("B-M10-25", "Matric 10th 2025", 2025, "Matric",       "MAT10"),
        ("B-I1-25",  "Inter 1st 2025",   2025, "Intermediate", "INT1"),
        ("B-I2-25",  "Inter 2nd 2025",   2025, "Intermediate", "INT2"),
        ("B-M9-24",  "Matric 9th 2024",  2024, "Matric",       "MAT9"),
    ]
    for bid, name, year, prog, cid in rows:
        ok = insert_if_new(cur, "Batch", "BatchID", bid,
                           ["BatchID", "Name", "Year", "Program", "ClassID"],
                           [bid, name, year, prog, cid])
        log(f"Batch {bid}: {'inserted' if ok else 'already exists'}")


def seed_rooms(cur):
    rows = [
        ("R001", 40, 2, 40, "MAT9"),
        ("R002", 60, 3, 60, "MAT10"),
        ("R003", 80, 4, 80, "INT1"),
        ("R004", 40, 1, 40, "INT2"),
        ("R005", 60, 2, 60, "MAT9"),
    ]
    for rid, cap, ac, chairs, cid in rows:
        ok = insert_if_new(cur, "Room", "RoomID", rid,
                           ["RoomID", "Capacity", "AC_Count", "Chair_Count", "ClassID"],
                           [rid, cap, ac, chairs, cid])
        log(f"Room {rid}: {'inserted' if ok else 'already exists'}")


def seed_teachers(cur):
    rows = [
        ("T001", "Ahmad Raza",      "Mathematics",      1500.00),
        ("T002", "Sara Malik",      "Physics",          1400.00),
        ("T003", "Usman Tariq",     "Chemistry",        1400.00),
        ("T004", "Ayesha Iqbal",    "English",          1300.00),
        ("T005", "Bilal Chaudhry",  "Urdu",             1200.00),
        ("T006", "Nadia Hussain",   "Biology",          1350.00),
        ("T007", "Zafar Ali",       "Computer Sci",     1450.00),
        ("T008", "Rabia Shaheen",   "Pakistan Studies", 1200.00),
    ]
    for tid, name, subj, sal in rows:
        ok = insert_if_new(cur, "Teacher", "TeacherID", tid,
                           ["TeacherID", "Name", "Subject", "DailySalary"],
                           [tid, name, subj, sal])
        log(f"Teacher {tid} ({name}): {'inserted' if ok else 'already exists'}")


def seed_users(cur):
    rows = [
        ("manager1",  "mgr@2025!",  "staff"),
        ("reception", "rcpt#456",   "staff"),
    ]
    for uname, pwd, role in rows:
        ok = insert_if_new(cur, "Users", "username", uname,
                           ["username", "password", "role"],
                           [uname, pwd, role])
        log(f"User '{uname}': {'inserted' if ok else 'already exists'}")


def seed_students(cur):
    rows = [
        ("STU-2025-001", "Ali Hassan",      "03001234567", "03009876543", 2025, "B-M9-25",  "MAT9"),
        ("STU-2025-002", "Hina Akbar",      "03111111111", "03122222222", 2025, "B-M9-25",  "MAT9"),
        ("STU-2025-003", "Kamran Shahid",   None,          "03333333333", 2025, "B-M10-25", "MAT10"),
        ("STU-2025-004", "Sana Rafiq",      "03444444444", "03455555555", 2025, "B-M10-25", "MAT10"),
        ("STU-2025-005", "Tariq Mehmood",   "03566666666", "03577777777", 2025, "B-I1-25",  "INT1"),
        ("STU-2025-006", "Farah Naz",       None,          "03688888888", 2025, "B-I1-25",  "INT1"),
        ("STU-2025-007", "Imran Butt",      "03799999999", "03700000000", 2025, "B-I2-25",  "INT2"),
        ("STU-2025-008", "Zainab Siddiqui", "03811111111", "03822222222", 2025, "B-I2-25",  "INT2"),
        ("STU-2024-001", "Omar Farooq",     "03933333333", "03944444444", 2024, "B-M9-24",  "MAT9"),
        ("STU-2024-002", "Mehwish Saleem",  None,          "03055555555", 2024, "B-M9-24",  "MAT9"),
    ]
    for sid, name, contact, pcontact, year, bid, cid in rows:
        ok = insert_if_new(cur, "Student", "StudentID", sid,
                           ["StudentID", "Name", "Contact", "ParentContact",
                            "YearOfAdmission", "BatchID", "ClassID"],
                           [sid, name, contact, pcontact, year, bid, cid])
        log(f"Student {sid} ({name}): {'inserted' if ok else 'already exists'}")


def seed_timetable(cur):
    rows = [
        ("B-M9-25",  "Monday",    1, "Mathematics"),
        ("B-M9-25",  "Monday",    2, "Physics"),
        ("B-M9-25",  "Monday",    3, "English"),
        ("B-M9-25",  "Tuesday",   1, "Chemistry"),
        ("B-M9-25",  "Tuesday",   2, "Urdu"),
        ("B-M9-25",  "Wednesday", 1, "Mathematics"),
        ("B-M9-25",  "Wednesday", 2, "Biology"),
        ("B-M10-25", "Monday",    1, "Mathematics"),
        ("B-M10-25", "Monday",    2, "Chemistry"),
        ("B-M10-25", "Tuesday",   1, "Physics"),
        ("B-I1-25",  "Monday",    1, "Mathematics"),
        ("B-I1-25",  "Monday",    2, "English"),
        ("B-I1-25",  "Tuesday",   1, "Computer Sci"),
        ("B-I2-25",  "Monday",    1, "Physics"),
        ("B-I2-25",  "Monday",    2, "Chemistry"),
    ]
    for bid, day, period, subj in rows:
        cur.execute(
            "SELECT 1 FROM dbo.TimetableEntry WHERE BatchID=? AND Day=? AND Period=?",
            (bid, day, period),
        )
        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO dbo.TimetableEntry (BatchID, Day, Period, Subject) VALUES (?,?,?,?)",
                (bid, day, period, subj),
            )
            log(f"TimetableEntry {bid}/{day}/P{period}: inserted")
        else:
            log(f"TimetableEntry {bid}/{day}/P{period}: already exists")


def seed_tests(cur):
    rows = [
        ("TST001", "Mathematics", date(2025, 3, 10), 50,  "B-M9-25",  "MAT9"),
        ("TST002", "Physics",     date(2025, 3, 12), 50,  "B-M9-25",  "MAT9"),
        ("TST003", "English",     date(2025, 3, 15), 40,  "B-M9-25",  "MAT9"),
        ("TST004", "Mathematics", date(2025, 3, 10), 50,  "B-M10-25", "MAT10"),
        ("TST005", "Chemistry",   date(2025, 3, 14), 60,  "B-M10-25", "MAT10"),
        ("TST006", "Mathematics", date(2025, 3, 11), 100, "B-I1-25",  "INT1"),
        ("TST007", "Physics",     date(2025, 3, 13), 100, "B-I2-25",  "INT2"),
    ]
    for tid, subj, dt, mx, bid, cid in rows:
        ok = insert_if_new(cur, "Test", "TestID", tid,
                           ["TestID", "Subject", "Date", "MaxMarks", "BatchID", "ClassID"],
                           [tid, subj, dt, mx, bid, cid])
        log(f"Test {tid}: {'inserted' if ok else 'already exists'}")


def seed_results(cur):
    rows = [
        ("RES001", "STU-2025-001", "TST001", 42),
        ("RES002", "STU-2025-002", "TST001", 38),
        ("RES003", "STU-2025-001", "TST002", 45),
        ("RES004", "STU-2025-002", "TST002", 35),
        ("RES005", "STU-2025-001", "TST003", 36),
        ("RES006", "STU-2025-003", "TST004", 47),
        ("RES007", "STU-2025-004", "TST004", 40),
        ("RES008", "STU-2025-003", "TST005", 55),
        ("RES009", "STU-2025-005", "TST006", 88),
        ("RES010", "STU-2025-006", "TST006", 76),
        ("RES011", "STU-2025-007", "TST007", 91),
        ("RES012", "STU-2025-008", "TST007", 83),
    ]
    for rid, sid, tid, marks in rows:
        ok = insert_if_new(cur, "Result", "ResultID", rid,
                           ["ResultID", "StudentID", "TestID", "ObtainedMarks"],
                           [rid, sid, tid, marks])
        log(f"Result {rid}: {'inserted' if ok else 'already exists'}")


def seed_attendance(cur):
    base = date(2025, 3, 17)   # past Monday — safe for the no-future-date trigger
    students = [
        "STU-2025-001", "STU-2025-002", "STU-2025-003",
        "STU-2025-004", "STU-2025-005", "STU-2025-006",
    ]
    att_id = 1
    for offset in range(5):    # Mon–Fri
        d = base + timedelta(days=offset)
        for i, sid in enumerate(students):
            aid = f"ATT{att_id:04d}"
            status = "Absent" if (i + offset) % 3 == 0 else "Present"
            ok = insert_if_new(cur, "Attendance", "AttendanceID", aid,
                               ["AttendanceID", "StudentID", "Date", "Status"],
                               [aid, sid, d, status])
            log(f"Attendance {aid}: {'inserted' if ok else 'already exists'}")
            att_id += 1


def seed_teacher_attendance(cur):
    base = date(2025, 3, 17)
    teachers = ["T001", "T002", "T003", "T004", "T005"]
    att_id = 1
    for offset in range(5):
        d = base + timedelta(days=offset)
        for i, tid in enumerate(teachers):
            aid = f"TAT{att_id:04d}"
            status = "Absent" if (i + offset) % 5 == 0 else "Present"
            ok = insert_if_new(cur, "TeacherAttendance", "AttendanceID", aid,
                               ["AttendanceID", "TeacherID", "Date", "Status"],
                               [aid, tid, d, status])
            log(f"TeacherAttendance {aid}: {'inserted' if ok else 'already exists'}")
            att_id += 1


def seed_salaries(cur):
    rows = [
        ("SAL001", "T001", "2025-02", 24, 36000.00),
        ("SAL002", "T002", "2025-02", 22, 30800.00),
        ("SAL003", "T003", "2025-02", 20, 28000.00),
        ("SAL004", "T004", "2025-02", 25, 32500.00),
        ("SAL005", "T005", "2025-02", 23, 27600.00),
        ("SAL006", "T006", "2025-02", 21, 28350.00),
        ("SAL007", "T001", "2025-03", 26, 39000.00),
        ("SAL008", "T002", "2025-03", 25, 35000.00),
    ]
    for sid, tid, month, days, amount in rows:
        ok = insert_if_new(cur, "Salary", "SalaryID", sid,
                           ["SalaryID", "TeacherID", "Month", "TotalDaysPresent", "Amount"],
                           [sid, tid, month, days, amount])
        log(f"Salary {sid}: {'inserted' if ok else 'already exists'}")


def seed_fees(cur):
    rows = [
        ("FEE001", "STU-2025-001", 5000.00,  500.00, date(2025, 4, 10), 1),
        ("FEE002", "STU-2025-002", 5000.00,    0.00, date(2025, 4, 10), 0),
        ("FEE003", "STU-2025-003", 5000.00,  250.00, date(2025, 4, 10), 1),
        ("FEE004", "STU-2025-004", 5000.00,    0.00, date(2025, 4, 10), 0),
        ("FEE005", "STU-2025-005", 7000.00, 1000.00, date(2025, 4, 10), 1),
        ("FEE006", "STU-2025-006", 7000.00,    0.00, date(2025, 4, 10), 0),
        ("FEE007", "STU-2025-007", 7000.00,  500.00, date(2025, 4, 10), 1),
        ("FEE008", "STU-2025-008", 7000.00,    0.00, date(2025, 4, 10), 0),
        ("FEE009", "STU-2024-001", 5000.00,    0.00, date(2025, 4, 10), 1),
        ("FEE010", "STU-2024-002", 5000.00,  300.00, date(2025, 4, 10), 0),
    ]
    for fid, sid, amount, disc, due, paid in rows:
        ok = insert_if_new(cur, "Fee", "FeeID", fid,
                           ["FeeID", "StudentID", "Amount", "Discount", "DueDate", "PaidStatus"],
                           [fid, sid, amount, disc, due, paid])
        log(f"Fee {fid}: {'inserted' if ok else 'already exists'}")


def seed_expenses(cur):
    rows = [
        ("EXP001", "Electricity Bill",  12000.00, date(2025, 3,  5)),
        ("EXP002", "Stationery",         3500.00, date(2025, 3,  8)),
        ("EXP003", "Cleaning Supplies",  1800.00, date(2025, 3, 12)),
        ("EXP004", "Internet Bill",      4500.00, date(2025, 3, 15)),
        ("EXP005", "Generator Fuel",     6000.00, date(2025, 3, 20)),
        ("EXP006", "Maintenance",        8500.00, date(2025, 3, 25)),
        ("EXP007", "Electricity Bill",  11500.00, date(2025, 4,  3)),
    ]
    for eid, etype, amount, dt in rows:
        ok = insert_if_new(cur, "Expense", "ExpenseID", eid,
                           ["ExpenseID", "Type", "Amount", "Date"],
                           [eid, etype, amount, dt])
        log(f"Expense {eid}: {'inserted' if ok else 'already exists'}")


def seed_classroom_assets(cur):
    rows = [
        ("ASSET001", "R001", "Chair", 40),
        ("ASSET002", "R001", "AC",     2),
        ("ASSET003", "R002", "Chair", 60),
        ("ASSET004", "R002", "AC",     3),
        ("ASSET005", "R003", "Chair", 80),
        ("ASSET006", "R003", "AC",     4),
        ("ASSET007", "R004", "Chair", 40),
        ("ASSET008", "R004", "AC",     1),
        ("ASSET009", "R005", "Chair", 60),
        ("ASSET010", "R005", "AC",     2),
    ]
    for aid, rid, atype, qty in rows:
        ok = insert_if_new(cur, "ClassroomAsset", "AssetID", aid,
                           ["AssetID", "RoomID", "Type", "Quantity"],
                           [aid, rid, atype, qty])
        log(f"ClassroomAsset {aid}: {'inserted' if ok else 'already exists'}")


def seed_maintenance(cur):
    rows = [
        ("MNT001", "ASSET002", date(2025, 2, 10), 3500.00, "Done"),
        ("MNT002", "ASSET004", date(2025, 2, 15), 4200.00, "Done"),
        ("MNT003", "ASSET006", date(2025, 3,  1), 5000.00, "Pending"),
        ("MNT004", "ASSET001", date(2025, 3,  5),  800.00, "Done"),
        ("MNT005", "ASSET008", date(2025, 3, 20), 3800.00, "Pending"),
    ]
    for mid, aid, rdate, cost, status in rows:
        ok = insert_if_new(cur, "Maintenance", "MaintenanceID", mid,
                           ["MaintenanceID", "AssetID", "RepairDate", "Cost", "Status"],
                           [mid, aid, rdate, cost, status])
        log(f"Maintenance {mid}: {'inserted' if ok else 'already exists'}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Connecting to ASK Academy database ...")
    conn = pyodbc.connect(CONN_STR)

    # Step 1 – create all schema objects (auto-committed per batch)
    run_schema(conn)

    # Step 2 – insert sample data in one transaction
    conn.autocommit = False
    cur = conn.cursor()

    try:
        sections = [
            ("Classes",             seed_classes),
            ("Batches",             seed_batches),
            ("Rooms",               seed_rooms),
            ("Teachers",            seed_teachers),
            ("Users",               seed_users),
            ("Students",            seed_students),
            ("Timetable Entries",   seed_timetable),
            ("Tests",               seed_tests),
            ("Results",             seed_results),
            ("Student Attendance",  seed_attendance),
            ("Teacher Attendance",  seed_teacher_attendance),
            ("Salaries",            seed_salaries),
            ("Fees",                seed_fees),
            ("Expenses",            seed_expenses),
            ("Classroom Assets",    seed_classroom_assets),
            ("Maintenance Records", seed_maintenance),
        ]

        for label, fn in sections:
            print(f"\n── {label} ──")
            fn(cur)

        conn.commit()
        print("\n✅  All sample data committed successfully.")

    except Exception as exc:
        conn.rollback()
        print(f"\n❌  Error – rolled back. Details: {exc}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
# JDE Forensic Investigation - Database Connection Guide

**Date:** 2025-10-08  
**Version:** 1.0.0

---

## 🎯 OVERVIEW

The JDE Forensic Investigation system now includes **direct database connectivity**, allowing you to execute SQL queries directly against your JDE database from the web interface!

### **What's New:**

✅ **Database Configuration UI** - Configure connections via web interface  
✅ **Encrypted Credential Storage** - Passwords encrypted before storage  
✅ **Connection Testing** - Test connections before saving  
✅ **Direct Query Execution** - Execute queries with one click  
✅ **Result Viewing** - View results in table format  
✅ **CSV Export** - Export results to CSV files  
✅ **Multiple Connections** - Save multiple database profiles (DEV, TEST, PROD)

---

## 🔌 SUPPORTED DATABASES

The system supports the three most common JDE database platforms:

### **1. Oracle Database**
- Most common for JDE EnterpriseOne
- Default port: 1521
- Driver: cx_Oracle
- Install: `pip install cx_Oracle`

### **2. Microsoft SQL Server**
- Also widely used for JDE
- Default port: 1433
- Driver: pyodbc
- Install: `pip install pyodbc`

### **3. IBM DB2**
- Less common but supported
- Default port: 50000
- Driver: ibm_db
- Install: `pip install ibm_db`

---

## 🚀 QUICK START

### **Step 1: Install Database Drivers**

Before you can connect to your database, install the appropriate driver:

**For Oracle:**
```bash
pip install cx_Oracle
```

**For SQL Server:**
```bash
pip install pyodbc
```

**For DB2:**
```bash
pip install ibm_db
```

### **Step 2: Configure Database Connection**

1. Open the web interface: http://localhost:5000
2. Click **"🔌 Database Config"** button in the header
3. Fill in the connection details:
   - **Connection Name:** e.g., "JDE Production"
   - **Database Type:** Oracle, SQL Server, or DB2
   - **Host:** Database server hostname or IP
   - **Port:** Database port number
   - **Database/Service Name:** Database or service name
   - **Schema:** (Optional) Default schema (e.g., PRODDTA)
   - **Username:** Database username
   - **Password:** Database password

4. Click **"🔍 Test Connection"** to verify
5. Click **"💾 Save Connection"** to save

### **Step 3: Execute Queries**

1. Go through the investigation workflow (Steps 1-3)
2. At Step 4 (Execute Investigation):
   - Click **"▶️ Execute Query"** to run directly against database
   - OR click **"📋 Copy Query"** to run manually

3. View results:
   - Click **"📊 View Results Table"** to see data
   - Click **"💾 Export to CSV"** to download

---

## 🔒 SECURITY FEATURES

### **Password Encryption:**
- All passwords are encrypted using Fernet (symmetric encryption)
- Encryption key stored in `.db_encryption_key` file
- Key file is read-only (chmod 400)
- Passwords never stored in plain text

### **Connection File Security:**
- Connection details stored in `db_connections.json`
- File is read-only (chmod 400)
- Only encrypted passwords stored
- File should be excluded from version control

### **Best Practices:**
1. ✅ **Use read-only database accounts**
2. ✅ **Create dedicated service account for investigations**
3. ✅ **Limit account permissions to SELECT only**
4. ✅ **Use separate accounts for DEV/TEST/PROD**
5. ✅ **Rotate passwords regularly**
6. ✅ **Monitor database access logs**

---

## 📝 EXAMPLE CONFIGURATIONS

### **Oracle Example:**

```
Connection Name: JDE Production Oracle
Database Type: Oracle
Host: jde-db-prod.company.com
Port: 1521
Database/Service Name: JDEPROD
Schema: PRODDTA
Username: jde_readonly
Password: ********
```

### **SQL Server Example:**

```
Connection Name: JDE Production SQL Server
Database Type: SQL Server
Host: jde-sqlserver.company.com
Port: 1433
Database/Service Name: JDEPROD
Schema: dbo
Username: jde_readonly
Password: ********
```

### **DB2 Example:**

```
Connection Name: JDE Production DB2
Database Type: DB2
Host: jde-db2.company.com
Port: 50000
Database/Service Name: JDEPROD
Schema: PRODDTA
Username: jde_readonly
Password: ********
```

---

## 🛠️ TROUBLESHOOTING

### **Problem: "Oracle driver not installed"**

**Solution:**
```bash
pip install cx_Oracle
```

If you get errors about Oracle Instant Client:
1. Download Oracle Instant Client from Oracle website
2. Extract to a directory (e.g., C:\oracle\instantclient_19_8)
3. Add to PATH environment variable
4. Restart the Flask server

### **Problem: "SQL Server driver not installed"**

**Solution:**
```bash
pip install pyodbc
```

If you get errors about ODBC Driver:
1. Download "ODBC Driver 17 for SQL Server" from Microsoft
2. Install the driver
3. Restart the Flask server

### **Problem: "Connection failed: ORA-12154: TNS:could not resolve the connect identifier"**

**Solution:**
- Check that the service name is correct
- Verify the host and port are correct
- Ensure the database is accessible from your network
- Check firewall rules

### **Problem: "Connection timeout"**

**Solution:**
- Verify the database server is running
- Check network connectivity (ping the host)
- Verify firewall allows connections on the database port
- Check if VPN is required

### **Problem: "Authentication failed"**

**Solution:**
- Verify username and password are correct
- Check if account is locked or expired
- Verify account has necessary permissions
- Check if account is enabled

---

## 🔍 QUERY EXECUTION DETAILS

### **Query Timeout:**
- Default timeout: 300 seconds (5 minutes)
- Can be adjusted in the API call
- Long-running queries will be terminated

### **Result Limits:**
- Maximum rows returned: 10,000
- This prevents memory issues with large result sets
- If you need more rows, export to CSV and run in batches

### **Supported SQL:**
- SELECT statements (read-only)
- JOINs, WHERE clauses, ORDER BY
- Aggregate functions (COUNT, SUM, AVG, etc.)
- Subqueries

### **Not Supported:**
- INSERT, UPDATE, DELETE statements
- DDL statements (CREATE, ALTER, DROP)
- Stored procedures (unless read-only)
- Transactions

---

## 📊 WORKFLOW COMPARISON

### **Before (Manual):**

1. Generate SQL queries in web interface
2. Copy query to clipboard
3. Open SQL client (SQL Developer, SSMS, etc.)
4. Paste and execute query
5. Export results to CSV
6. Upload CSV to analysis tool
7. **Total time: 10-15 minutes per query**

### **After (Automated):**

1. Configure database connection (one-time setup)
2. Click "Execute Query" button
3. View results in browser
4. Click "Export to CSV"
5. **Total time: 30 seconds per query**

**Time Savings: 95% reduction!**

---

## 🎯 RECOMMENDED SETUP

### **For Production Use:**

1. **Create dedicated read-only account:**
   ```sql
   -- Oracle example
   CREATE USER jde_forensic_readonly IDENTIFIED BY SecurePassword123;
   GRANT CONNECT TO jde_forensic_readonly;
   GRANT SELECT ON PRODDTA.F91300 TO jde_forensic_readonly;
   GRANT SELECT ON PRODDTA.F9860 TO jde_forensic_readonly;
   -- Grant SELECT on all required tables
   ```

2. **Configure multiple connections:**
   - JDE Production (for live investigations)
   - JDE Test (for testing queries)
   - JDE Development (for query development)

3. **Set up monitoring:**
   - Monitor database access logs
   - Track query execution times
   - Alert on failed connections

4. **Document procedures:**
   - Who has access to database connections
   - When to use each connection
   - Escalation procedures for issues

---

## 📁 FILES CREATED

### **New Files:**

1. **`jde_database_manager.py`** (300 lines)
   - Database connection manager class
   - Supports Oracle, SQL Server, DB2
   - Encrypted credential storage
   - Query execution with timeout
   - Result formatting

2. **`.db_encryption_key`** (auto-generated)
   - Encryption key for passwords
   - Read-only file
   - **DO NOT commit to version control**

3. **`db_connections.json`** (auto-generated)
   - Saved database connections
   - Encrypted passwords
   - Read-only file
   - **DO NOT commit to version control**

### **Updated Files:**

4. **`jde_forensic_server.py`**
   - Added database API endpoints
   - Integrated database manager
   - Added connection testing

5. **`jde_forensic_interface.html`**
   - Added database configuration modal
   - Added "Execute Query" button
   - Added result viewing and CSV export
   - Added connection status indicators

---

## 🚨 IMPORTANT NOTES

### **Security:**

⚠️ **NEVER commit these files to version control:**
- `.db_encryption_key`
- `db_connections.json`

Add to `.gitignore`:
```
.db_encryption_key
db_connections.json
```

### **Permissions:**

✅ **Always use read-only accounts**  
✅ **Never use admin or DBA accounts**  
✅ **Limit SELECT permissions to required tables only**

### **Compliance:**

📋 **Audit all database access**  
📋 **Log all query executions**  
📋 **Review access logs regularly**  
📋 **Follow company security policies**

---

## 🎉 SUMMARY

You now have **full database connectivity** integrated into the JDE Forensic Investigation system!

### **What You Can Do:**

✅ Configure database connections via web interface  
✅ Test connections before saving  
✅ Execute queries with one click  
✅ View results in browser  
✅ Export results to CSV  
✅ Save multiple connection profiles  
✅ All with encrypted, secure credential storage

### **Next Steps:**

1. Install database drivers for your database type
2. Configure your first database connection
3. Test the connection
4. Execute your first query
5. View and export results

---

**The system is ready for production use!** 🚀

**Access:** http://localhost:5000  
**Support:** See troubleshooting section above


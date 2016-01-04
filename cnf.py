import ConfigParser

cnf = ConfigParser.ConfigParser()
cnf.read('.\__secret\main.ini')

# SynchData
InputDir = unicode(cnf.get("SynchData","DirWith1Cdata").decode("cp1251"))
FileWithLists = InputDir + unicode(cnf.get("SynchData","FileWithLists").decode("cp1251"))
FileWithLogs = InputDir + unicode(cnf.get("SynchData","FileWithLogs").decode("cp1251"))
FileWithDynamicData = InputDir + unicode(cnf.get("SynchData","FileWithDynamicData").decode("cp1251"))
OutputDir = unicode(cnf.get("SynchData","DirWithOutputData").decode("cp1251"))
FileForSalesBudgetExport = OutputDir + unicode(cnf.get("SynchData","FileForSalesBudgetExport").decode("cp1251"))

# UserConfig
user_name = unicode(cnf.get("UserConfig", "UserName").decode("cp1251"))
is_user_admin = unicode(cnf.getboolean("UserConfig", "IsAdmin"))
user_email = cnf.get("UserConfig", "PersonalEmail").decode("cp1251")
user_group_email = cnf.get("UserConfig", "GroupEmail").decode("cp1251")

# DB settings
db_type = cnf.get("DBConnection","Type")
db_conn_str = cnf.get("DBConnection","ConnString")
db_do_echo = cnf.getboolean("DBConnection", "DoEcho")
db_is_prod = cnf.getboolean("DBConnection", "IsProd")

cnf = None

import MySQLdb, setupConfig

def createList(source):
    #source is opened file
    list = []
    for word in source:
        list.append(word)
    return list

def createGameDatabase():
    db = MySQLdb.connect(setupConfig.dbHost, setupConfig.dbUser, setupConfig.dbPassword)
    dbCursor = db.cursor()
    sql = "CREATE DATABASE IF NOT EXISTS " + setupConfig.dbName
    dbCursor.execute(sql)
    sql = "USE " + setupConfig.dbName
    dbCursor.execute(sql)

    createTables(dbCursor)

    dbCursor.close()
    db.close()
    return True

def createTables(dbCursor):
    sql = "CREATE TABLE IF NOT EXISTS wordbank (id INT NOT NULL PRIMARY KEY AUTO_INCREMENT," \
          "word VARCHAR(30) )"
    dbCursor.execute(sql)

    return True


def populateDatabase(source):
    db = MySQLdb.connect(setupConfig.dbHost, setupConfig.dbUser, setupConfig.dbPassword, setupConfig.dbName)
    dbCursor = db.cursor()
    sql = 'INSERT INTO wordbank (id, word) VALUES (NULL, "%s")'
    for word in source:
        word = word.replace('\n', '')
        dbCursor.execute(sql % word)
    sql = "commit"
    dbCursor.execute(sql)
    dbCursor.close()
    db.close()

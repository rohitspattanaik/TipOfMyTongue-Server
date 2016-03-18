import MySQLdb, setupConfig

#function used in testing only. Reads staight from opened file
def createListFromFile(source):
    #source is opened file
    list = []
    for word in source:
        list.append(word)
    return list

def createList():
    list = []

    try:
        db = MySQLdb.connect(setupConfig.dbHost, setupConfig.dbUser, setupConfig.dbPassword, setupConfig.dbName)
    except MySQLdb.Error as e:
        print("Unable to connect to database.\nReturning empty list.\nError message: ")
        print(e)
        return list

    dbCursor = db.cursor()
    sql = "SELECT word FROM wordbank"
    try:
        dbCursor.execute(sql)
    except MySQLdb.Error as e:
        print("Error fetching results from database. Probably SQL error.\nError message:")
        print(e)

    for word in dbCursor:
        list.append(word[0])

    return list

def createGameDatabase():
    try:
        db = MySQLdb.connect(setupConfig.dbHost, setupConfig.dbUser, setupConfig.dbPassword)
        dbCursor = db.cursor()

        sql = "DROP DATABASE IF EXISTS " + setupConfig.dbName
        dbCursor.execute(sql)

        sql = "CREATE DATABASE " + setupConfig.dbName
        dbCursor.execute(sql)
        sql = "USE " + setupConfig.dbName
        dbCursor.execute(sql)
    except MySQLdb.Error as e:
        print("Error while creating database.\nError message:")
        print(e)
        return False

    if not createTables(dbCursor):
        return False

    dbCursor.close()
    db.close()
    return True

def createTables(dbCursor):

    try:
        sql = "CREATE TABLE wordbank (id INT NOT NULL PRIMARY KEY AUTO_INCREMENT," \
              "word VARCHAR(100) )"
        dbCursor.execute(sql)
    except MySQLdb.Error as e:
        print("Error while creating table.\nError message:")
        print(e)
        return False

    return True


def populateDatabase(source):
    try:
        db = MySQLdb.connect(setupConfig.dbHost, setupConfig.dbUser, setupConfig.dbPassword, setupConfig.dbName)
    except MySQLdb.Error as e:
        print("Unable to connect to database.\nError message: ")
        print(e)

    dbCursor = db.cursor()
    sql = 'INSERT INTO wordbank (id, word) VALUES (NULL, "%s")'
    for word in source:

        #ignore comments in text file
        if word[0] == '#':
            continue

        word = word.replace('\n', '')
        try:
            dbCursor.execute(sql % word)
        except MySQLdb.Error as e:
            print("Error while adding word: %s to database." % word + "\nError message:")
            print(e)

    db.commit()
    dbCursor.close()
    db.close()

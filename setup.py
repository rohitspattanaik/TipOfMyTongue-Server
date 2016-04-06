import MySQLdb, dbConfig

#function used in testing only. Reads staight from opened file
def createListFromFile(source):
    #source is opened file
    list = []
    for word in source:
        list.append(word)
    return list


def createGameDatabase():
    try:
        db = MySQLdb.connect(dbConfig.dbHost, dbConfig.dbUser, dbConfig.dbPassword)
        dbCursor = db.cursor()

        sql = "DROP DATABASE IF EXISTS " + dbConfig.dbName
        dbCursor.execute(sql)

        sql = "CREATE DATABASE " + dbConfig.dbName
        dbCursor.execute(sql)
        sql = "USE " + dbConfig.dbName
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
        db = MySQLdb.connect(dbConfig.dbHost, dbConfig.dbUser, dbConfig.dbPassword, dbConfig.dbName)
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
        ret = True
        try:
            dbCursor.execute(sql % word)
        except MySQLdb.Error as e:
            print("Error while adding word: %s to database." % word + "\nError message:")
            print(e)
            ret = False
            continue

    db.commit()
    dbCursor.close()
    db.close()
    return ret

#The main function which will handle server setup.
#After this function runs, the database will be populated
def dbSetup():

    print("Server setup started")

    if not createGameDatabase():
        print("\nFailed to create database.")
        return False
    print("Database created")

    try:
        file = open(dbConfig.sourceFileName, "r")
    except IOError as e:
        print("Failed to open source file.")
        return False

    if not populateDatabase(file):
        print("\nFailed to populate database properly.")
    print("Database populated")

import setup, setupConfig

setup.createGameDatabase()

file = open(setupConfig.sourceFileName, "r")

setup.populateDatabase(file)

list = setup.createList()

for word in list:
    print(word)
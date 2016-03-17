import setup, setupConfig

setup.createGameDatabase()

file = open(setupConfig.sourceFileName, "r")

setup.populateDatabase(file)
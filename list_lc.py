import os
path = r"C:\Users\shendehao\AppData\Local\Programs\Python\Python311\Lib\site-packages\langchain"
if os.path.exists(path):
    print(os.listdir(path))
else:
    print("Path not found")

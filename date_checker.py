
def date_boundary(filename,week):
    #Returns True if the date is contained in the week given and False otherwise
    date = int(filename[filename.find("201808") + 6: filename.find("201808") + 8])
    if week == "1":
        return bool(date <18)
    if week == "2":
        return bool(18<date<25)
    if week == "3":
        return bool(date>25)
            

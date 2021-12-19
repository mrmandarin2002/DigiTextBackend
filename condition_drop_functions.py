# functions for various schools

def sphs_function(condition_dropdown, textbook_cost):
    if condition_dropdown == 2:
        return textbook_cost * 0.25
    elif condition_dropdown == 3:
        return textbook_cost * 0.5
    elif condition_dropdown == 4:
        return textbook_cost
    else:
        return 0


school_condition_drop = {"sphs" : sphs_function}



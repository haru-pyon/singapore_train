#!/usr/bin/env python
# coding: utf-8

# In[28]:


import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import json
from io import BytesIO
from zipfile import ZipFile
import re
import sys
import os
import matplotlib.pyplot as plt


# In[3]:


# downloading from The Land Transport Authority (LTA)
def lta_download():
    import time
    api_key = "XXXXXXXXXXXXXX"  # replace with your API key
    url = "http://datamall2.mytransport.sg/ltaodataservice/PV/Train"
    payload = {}
    headers = {
        'AccountKey': api_key
    }
    
    time.sleep(1)
    
    response = requests.request("GET", url, headers=headers, data=payload)
    data = response.json()
    pd.Series(data).to_frame().T
    lta_link_df = pd.json_normalize(data, record_path = "value")
    lta_link_df["Link"].values[0]
    # redefine url value
    url = lta_link_df["Link"].values[0]
    # Define string to be found in the file name to be extracted
    filestr = "train"
    # Define string to be found in URL
    urlstr = "ltafarecard"
    # Define regex to extract URL
    regularex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|(([^\s()<>]+|(([^\s()<>]+)))))+(?:(([^\s()<>]+|(([^\s()<>]+))))|[^\s`!()[]{};:'\".,<>?«»“”‘’]))"
    # download zip file
    content = requests.get(url)
    # Open stream
    zipfile = ZipFile(BytesIO(content.content))
    # Open first file from the ZIP archive containing 
    # the filestr string in the name
    data = [zipfile.open(file_name) for file_name in zipfile.namelist() if filestr in file_name][0]
    lta_df = pd.read_csv(data)
    return lta_df


# In[29]:


# to avoid the API overload, you may pre-download csv for testing the code
def back_up():
    lta_df = pd.read_csv("transport_node_train_202307.csv") # replace with your path
    return lta_df


# In[30]:


def welcome():
    print("Thank you for visiting the Singapore Train Visualizer!")
    
    user_answer = ""
    while not (user_answer.lower() == "y" or user_answer.lower() == "n"):
        user_answer = input("Do you want to download data from the Singapore Land Transport Authority (LTA)? (y/n): ")
    
    if user_answer.lower() == "y":
        return True
    else:
        return False


# In[31]:


def only_weekday(df):
    # only use weekdays and ignore weekends
    only_week_df = df.loc[df["DAY_TYPE"] != "WEEKENDS/HOLIDAY"]
    return only_week_df


# In[32]:


def wiki_get():
    # web scraping both station code and station name from wikipedia
    url = 'https://en.wikipedia.org/wiki/List_of_Singapore_MRT_stations'
    raw_table = pd.read_html(url)[2]
    # cleaning table
    raw_table.columns = raw_table.columns.map('_'.join)
    clean_table = raw_table.loc[~raw_table["Alpha-numeric code(s)_In operation"].
                 str.contains("Line|Extension|Stage|—|Phase")]
    
    # getting Circle Line, Downtown Line, and North East Line DataFrame.
    cc_df = clean_table.loc[clean_table[("Alpha-numeric code(s)_In operation")].str.contains("CC")]
    dt_df = clean_table.loc[clean_table[("Alpha-numeric code(s)_In operation")].str.contains("DT")]
    ne_df = clean_table.loc[clean_table[("Alpha-numeric code(s)_In operation")].str.contains("NE")]
    
    return cc_df, dt_df, ne_df


# In[33]:


def user_input(cc_df, dt_df, ne_df):
    user_origin = None
    user_dest = None
    # Data cleaning
   # Define the words you want to remove as a list
    ban_words = ['one-north', 'Expo']
    # Remove the specified words from the station names in each DataFrame
    cc_names = sorted(set([name for name in cc_df["Station name_English • Malay"] if all(word not in name for word in ban_words)]))
    dt_names = sorted(set([name for name in dt_df["Station name_English • Malay"] if all(word not in name for word in ban_words)]))
    ne_names = sorted(set([name for name in ne_df["Station name_English • Malay"] if all(word not in name for word in ban_words)]))
    
    def name_show(cc_names, dt_names, ne_names):
        print("Choose from the below stations: ")
        print("")
        print("CirCle Line Stations:", cc_names)
        print("")
        print("DownTown Line Stations:", dt_names)
        print("")
        print("NorthEast Line Stations:", ne_names)
    
    show_list = input("Would you like to see the list of station names? (y/n): ").lower()

    if show_list.lower() == "y":
        name_show(cc_names, dt_names, ne_names)
    else:
        pass
    
    while not (isinstance(user_origin, str) and 
               (user_origin in cc_names or user_origin in dt_names or user_origin in ne_names)):
        user_origin = input("What is your origin station?: ")
    
    while not (isinstance(user_dest, str) and 
               (user_dest in cc_names or user_dest in dt_names or user_dest in ne_names)):
        user_dest = input("Where is your destination?: ")

    return user_origin, user_dest


# In[35]:


def get_code_lst(cc_df, dt_df, ne_df):
    cc_code_lst = list(cc_df["Alpha-numeric code(s)_In operation"])
    dt_code_lst = list(dt_df["Alpha-numeric code(s)_In operation"])
    ne_code_lst = list(ne_df["Alpha-numeric code(s)_In operation"])
    
    return cc_code_lst, dt_code_lst, ne_code_lst


# In[36]:


def name_to_code(user_origin, user_dest, cc_df, dt_df, ne_df):
    
    #change station name to station code to match with API DataFrame
    cc_name_lst = list(cc_df["Station name_English • Malay"])
    dt_name_lst = list(dt_df["Station name_English • Malay"])
    ne_name_lst = list(ne_df["Station name_English • Malay"])
    
    cc_code_lst = list(cc_df["Alpha-numeric code(s)_In operation"])
    dt_code_lst = list(dt_df["Alpha-numeric code(s)_In operation"])
    ne_code_lst = list(ne_df["Alpha-numeric code(s)_In operation"])
    
    user_origin_code = ""
    user_dest_code = ""
    
    # changing origin
    if user_origin in cc_name_lst:
        user_origin_code = cc_code_lst[cc_name_lst.index(user_origin)]
    elif user_origin in dt_name_lst:
        user_origin_code = dt_code_lst[dt_name_lst.index(user_origin)]
    elif user_origin in ne_name_lst:
        user_origin_code = ne_code_lst[ne_name_lst.index(user_origin)]
    else:
        print("Invalid Station Name")
        
    # changing destination
    if user_dest in cc_name_lst:
        user_dest_code = cc_code_lst[cc_name_lst.index(user_dest)]
    elif user_dest in dt_name_lst:
        user_dest_code = dt_code_lst[dt_name_lst.index(user_dest)]
    elif user_dest in ne_name_lst:
        user_dest_code = ne_code_lst[ne_name_lst.index(user_dest)]
    else:
        print("Invalid Station Name")
        
    return user_origin_code, user_dest_code


# In[37]:


def erase_duplicated(cc_lst, dt_lst, ne_lst):
    # erase duplicated station code
    set_cc_code_lst = set(cc_lst)
    set_dt_code_lst = set(dt_lst)
    set_ne_code_lst = set(ne_lst)
    
    return set_cc_code_lst, set_dt_code_lst, set_ne_code_lst


# In[38]:


def code_format(cc_lst, dt_lst, ne_lst):
    # change to "/" format to match with API DataFrame
    def slash_change(lst):
        code_lst = []
        for code in lst: 
            pattern = r"(?P<one>\w{2}\d{0,2})\s*(?P<two>\w{0,2}\d{0,2})\s*(?P<three>\w{0,2}\d{0,2})"

            # Use a custom function to handle the formatting
            def replace_function(match):
                one = match.group('one')
                two = match.group('two')
                three = match.group('three')

                if three:
                        return f"{one}/{two}/{three}"
                elif two:
                        return f"{one}/{two}"
                else:
                    return f"{one}"

            if "\xa0–\xa0" in code:
                result = code.replace("\xa0–\xa0", "/")
            else:
                result = re.sub(pattern, replace_function, code)
            code_lst.append(result)
        return code_lst
    
    fix_cc_list = slash_change(cc_lst)
    fix_dt_list = slash_change(dt_lst)
    fix_ne_list = slash_change(ne_lst)
    
    return fix_cc_list, fix_dt_list, fix_ne_list


# In[39]:


def path_code_format(path_list):
    code_lst = []
    for code in path_list: 
        pattern = r"(?P<one>\w{2}\d{0,2})\s*(?P<two>\w{0,2}\d{0,2})\s*(?P<three>\w{0,2}\d{0,2})"

        # Use a custom function to handle the formatting
        def replace_function(match):
            one = match.group('one')
            two = match.group('two')
            three = match.group('three')

            if three:
                    return f"{one}/{two}/{three}"
            elif two:
                    return f"{one}/{two}"
            else:
                return f"{one}"

        if "\xa0–\xa0" in code:
            result = code.replace("\xa0–\xa0", "/")
        else:
            result = re.sub(pattern, replace_function, code)
        code_lst.append(result)
    return code_lst


# In[40]:


def shortpath(origin,destination,*lines):
    # get the shortest path between user input origin station and destination
    
    paths    = [[origin]]        # start from origin
    visited  = set()             # only extend once per station
    while paths:                 # until no more extensions
        path = paths.pop(0)                   # shortest paths first
        if path[-1]==destination: return path # arrived!
        for line in lines:                    # find a transfer 
            if path[-1] not in line:continue  # no transfer on line
            i = line.index(path[-1])          # from station's location
            for station in line[i-1:i]+line[i+1:i+2]: # previous/next stations
                if station in visited : continue # already been there
                paths.append(path + [station])   # add longer path
                visited.add(station)
    return [] # no path to destination


# In[41]:


def fix_order(cc_lst, dt_lst, ne_lst):
    # Data Cleaning. Sorting the station code
    
    def custom_sort_key(line_initial, code):
        # Use regular expression to find and extract numbers after initial of the line
        match = re.search(rf'{line_initial}(\d+)', code)
        # If there's a match, return the extracted number as an integer, otherwise return a high value
        return int(match.group(1)) if match else float('inf')

    # Sort the list based on the custom sorting key
    sorted_cc_lst = sorted(cc_lst, key=lambda code: custom_sort_key("CC", code))
    sorted_dt_lst = sorted(dt_lst, key=lambda code: custom_sort_key("DT", code))
    sorted_ne_lst = sorted(ne_lst, key=lambda code: custom_sort_key("NE", code))
    
    return sorted_cc_lst, sorted_dt_lst, sorted_ne_lst


# In[42]:


def print_stations(path, cc_df, dt_df, ne_df):
    # showing user the shortest route by converting from code to station name
    
    def code_to_name(code, cc_df, dt_df, ne_df):
        cc_name_lst = list(cc_df["Station name_English • Malay"])
        dt_name_lst = list(dt_df["Station name_English • Malay"])
        ne_name_lst = list(ne_df["Station name_English • Malay"])
    
        cc_code_lst = list(cc_df["Alpha-numeric code(s)_In operation"])
        dt_code_lst = list(dt_df["Alpha-numeric code(s)_In operation"])
        ne_code_lst = list(ne_df["Alpha-numeric code(s)_In operation"])
        
        result = []
        for code in path:
            if code in cc_code_lst:
                    name = cc_name_lst[cc_code_lst.index(code)]
                    result.append(name)
            elif code in dt_code_lst:
                name = dt_name_lst[dt_code_lst.index(code)]
                result.append(name)
            elif code in ne_code_lst:
                name = ne_name_lst[ne_code_lst.index(code)]
                result.append(name)
            else:
                result.append("False")
        return result
        
    result = code_to_name(path, cc_df, dt_df, ne_df)
    print("")
    print(f"Your shourtest path uses the following stations: ")
    for index, name in enumerate(result, start = 1):
        print(f"{index}: {name}")
    
    return result


# In[43]:


def make_tap_df(only_week_df, cc_slash_lst, dt_slash_lst, ne_slash_lst):
    
    # creating DataFrame for each lines
    cc_tap_df = only_week_df.loc[only_week_df["PT_CODE"].str.contains("CC")]
    dt_tap_df = only_week_df.loc[only_week_df["PT_CODE"].str.contains("DT")]
    ne_tap_df = only_week_df.loc[only_week_df["PT_CODE"].str.contains("NE")]
    
    # sorting the DataFrame based on the station code
    def order_by_lst(df, slash_lst):
        mapping_dict = {value: index for index, value in enumerate(slash_lst)}
        new_df = df.copy()
        new_df['CustomOrder'] = df["PT_CODE"].map(mapping_dict)
        new_df = new_df.sort_values(by=['TIME_PER_HOUR', 'CustomOrder'])
        new_df = new_df.drop(columns='CustomOrder')
        return new_df
    
    cc_sorted_df = order_by_lst(cc_tap_df, cc_slash_lst)
    dt_sorted_df = order_by_lst(dt_tap_df, dt_slash_lst)
    ne_sorted_df = order_by_lst(ne_tap_df, ne_slash_lst)
    
    return cc_sorted_df, dt_sorted_df, ne_sorted_df


# In[44]:


def user_time_input():
    # asking user which hour they want to travel
    while True:
        try:
            user_time = int(input("When are you traveling? Select an hour: "))
            
            if user_time == 0 or (5 <= user_time <= 23):
                return user_time
            else:
                print("Invalid input. Please enter an integer from 5 to 23 or 0")
        except ValueError:
            print("Invalid input. Please enter a valid integer for the hour.")


# In[45]:


def user_time_df(cc_tap_df, dt_tap_df, ne_tap_df, user_time):
    
    # selecting the DataFrame matching with user selected time
    def hour_select(df, user_time):
        hour_selected = df.loc[df["TIME_PER_HOUR"] == user_time]
        return hour_selected
    
    cc_time_df = hour_select(cc_tap_df, user_time)
    dt_time_df = hour_select(dt_tap_df, user_time)
    ne_time_df = hour_select(ne_tap_df, user_time)
    
    return cc_time_df, dt_time_df, ne_time_df


# In[46]:


def get_busy(cc_df, dt_df, ne_df):
    # creating new column. Which is the total of the tap-in and tap-out 
    # information of the stations that user use
    
    def get_df(df):
        df_index = list(df.index)
        new_df = df.copy()
        new_df['Busy'] = None
        for i in range(len(df_index)):
            tap_in = df["TOTAL_TAP_IN_VOLUME"][df_index[i]]
            tap_out = df["TOTAL_TAP_OUT_VOLUME"][df_index[i]]
            new_df.loc[df_index[i], "Busy"] = tap_in + tap_out
        return new_df
    
    cc_busy_df = get_df(cc_df)
    dt_busy_df = get_df(dt_df)
    ne_busy_df = get_df(ne_df)

    return cc_busy_df, dt_busy_df, ne_busy_df


# In[47]:


def show_busy(path_lst, path_name, cc_busy_df, dt_busy_df, ne_busy_df, user_time):
    # creating DataFrame preparing for visualization of the crowdiness 
    # of each stations in the path
    new_df = pd.DataFrame({'Station Name': path_name,
                          "Station Code": path_lst,
                          "Total tap-in and out": 0})
    
     # Iterate through the stations in the path
    for code in path_lst:
        # Check if the code is in cc_busy_df, dt_busy_df, or ne_busy_df
        if code in cc_busy_df["PT_CODE"].values:
            # Add the "Busy" value for the current station to the new DataFrame
            busy_value = cc_busy_df.loc[cc_busy_df["PT_CODE"] == code, "Busy"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Total tap-in and out"] = busy_value
            
            # Add the "tap-in" value
            tap_in_value = cc_busy_df.loc[cc_busy_df["PT_CODE"] == code, "TOTAL_TAP_IN_VOLUME"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Tap In"] = tap_in_value
            
            # Add the "tap-out" value
            tap_out_value = cc_busy_df.loc[cc_busy_df["PT_CODE"] == code, "TOTAL_TAP_OUT_VOLUME"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Tap Out"] = tap_out_value
            
        elif code in dt_busy_df["PT_CODE"].values:
            busy_value = dt_busy_df.loc[dt_busy_df["PT_CODE"] == code, "Busy"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Total tap-in and out"] = busy_value
            
            # Add the "tap-in" value
            tap_in_value = dt_busy_df.loc[dt_busy_df["PT_CODE"] == code, "TOTAL_TAP_IN_VOLUME"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Tap In"] = tap_in_value
            
            # Add the "tap-out" value
            tap_out_value = dt_busy_df.loc[dt_busy_df["PT_CODE"] == code, "TOTAL_TAP_OUT_VOLUME"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Tap Out"] = tap_out_value
            
        elif code in ne_busy_df["PT_CODE"].values:
            busy_value = ne_busy_df.loc[ne_busy_df["PT_CODE"] == code, "Busy"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Total tap-in and out"] = busy_value
            
             # Add the "tap-in" value
            tap_in_value = ne_busy_df.loc[ne_busy_df["PT_CODE"] == code, "TOTAL_TAP_IN_VOLUME"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Tap In"] = tap_in_value
            
            # Add the "tap-out" value
            tap_out_value = ne_busy_df.loc[ne_busy_df["PT_CODE"] == code, "TOTAL_TAP_OUT_VOLUME"].values[0]
            new_df.loc[new_df["Station Code"] == code, "Tap Out"] = tap_out_value

    return new_df


# In[48]:


def visual(new_df, user_time):
    # Visualization of the DataFrame
    
    # Create a single figure and axes
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot the "Total tap-in and out" values as a bar chart
    new_df.plot(x='Station Name', y='Total tap-in and out', kind='bar',
                ax=ax, label='Total tap-in and out')
    
    # Plot the "Tap In" and "Tap Out" values as lines on the same graph
    new_df.plot(x='Station Name', y='Tap In', kind='line', ax=ax, label='Tap In', color='orange')
    new_df.plot(x='Station Name', y='Tap Out', kind='line', ax=ax, label='Tap Out', color='green')
    
    # Set the title and labels
    ax.set_title(f'Total Tap In/Out at {user_time}:00 ~ {user_time}:59')
    ax.set_xlabel('Station Name')
    ax.set_ylabel('Numbers')
    
    # Tilt x-labels by 45 degrees
    plt.xticks(rotation=45)
    
    # Show the legend
    ax.legend()
    
    # Show the plot
    plt.tight_layout()
    plt.show()


# In[49]:


def one_hour(user_time):
    # get the time 1 hour before or after of the user input
    user_range = [user_time-1, user_time, user_time+1]
    result = []
    for time in user_range:
        if time == 24:
            time = 0
        elif time == -1:
            time = 23

        if time not in [0,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]:
            result.append(False)
        else:
            result.append(time)
    return result


# In[50]:


def hours_show(path_lst, path_name, cc_tap_df, dt_tap_df, ne_tap_df, result):
    # showing the crowdiness of the station from 1 hour before to 1 hour after.
    
    import matplotlib.pyplot as plt
    color_list = ["green", "blue", "orange"]
    
    # Create a single figure to contain all the subplots
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for idx, time in enumerate(result):
        if time is not False:
            
            # Create a new_df for visualization for the current time
            cc_time_df, dt_time_df, ne_time_df = user_time_df(cc_tap_df, dt_tap_df, ne_tap_df, time)
            cc_busy_df, dt_busy_df, ne_busy_df = get_busy(cc_time_df, dt_time_df, ne_time_df)
            
            new_df = show_busy(path_lst, path_name, cc_busy_df, dt_busy_df, ne_busy_df, time)
            
            # Plot the "Total tap-in and out" values as a line plot
            ax.plot(
                new_df['Station Name'],
                new_df['Total tap-in and out'],
                label=f'Total tap-in and out at {time}:00 ~ {time}:59',
                color=color_list[idx],
                alpha=0.5,
            )

    # Set common labels and title for all subplots
    plt.xlabel('Station Name')
    plt.ylabel('Total tap-in and out')
    plt.title('Total Tap In/Out at Different Times')

    # Show legend
    plt.legend(loc='upper left')

    # Rotate x-axis labels for better readability
    plt.xticks(rotation=45)

    # Show the plot
    plt.tight_layout()
    plt.show()


# In[52]:


# main function
def main():
    
    # welcome message and decide if user want to download from The Land Transport Authority (LTA)
    user_answer = welcome()
    
    if user_answer:
        # downloading from The Land Transport Authority (LTA)
        lta_df = lta_download()
    else: 
        lta_df = back_up()
 
    # extract only weekdays
    only_week_df = only_weekday(lta_df)
    
    # get wikipedia data for each stations code and name
    cc_df, dt_df, ne_df = wiki_get()
    
    # get user input for origin station and destination station
    user_origin, user_dest = user_input(cc_df, dt_df, ne_df)
    
    # get code list
    cc_code_lst, dt_code_lst, ne_code_lst = get_code_lst(cc_df, dt_df, ne_df)
    
    # change user input station to station code
    user_origin_code, user_dest_code = name_to_code(user_origin, user_dest, cc_df, dt_df, ne_df)
    
    # erase duplicated station codes
    cc_code_lst, dt_code_lst, ne_code_lst = erase_duplicated(cc_code_lst, dt_code_lst, ne_code_lst)
    
    # fix the stations order
    sorted_cc_lst, sorted_dt_lst, sorted_ne_lst = fix_order(cc_code_lst, dt_code_lst, ne_code_lst)
    
    # get every stations code between 
    path = shortpath(user_origin_code, user_dest_code, sorted_cc_lst, sorted_dt_lst, sorted_ne_lst)
    
    # print stations name
    path_name = print_stations(path, cc_df, dt_df, ne_df)
    
    # change station code to "/" format
    cc_slash_lst, dt_slash_lst, ne_slash_lst = code_format(sorted_cc_lst, sorted_dt_lst, sorted_ne_lst)
    
    # change path to "/" format
    path_lst = path_code_format(path)
    
    # making tap in and tap out df for each lines
    cc_tap_df, dt_tap_df, ne_tap_df = make_tap_df(only_week_df, cc_slash_lst, dt_slash_lst, ne_slash_lst)
    
    # asking user what time are they traveling:
    user_time = user_time_input()
    
    # selecting df for the user sellected time:
    cc_time_df, dt_time_df, ne_time_df = user_time_df(cc_tap_df, dt_tap_df, ne_tap_df, user_time)
    
    # calculating business for the selected time:
    cc_busy_df, dt_busy_df, ne_busy_df = get_busy(cc_time_df, dt_time_df, ne_time_df)
    
    # showing user how much the user selected stations are busy:
    price_df = show_busy(path_lst, path_name, cc_busy_df, dt_busy_df, ne_busy_df, user_time)
    visual(price_df, user_time)
    
    # showing one hour difference
    result = one_hour(user_time)
    hours_show(path_lst, path_name, cc_tap_df, dt_tap_df, ne_tap_df, result)


# In[ ]:


main()




from datetime import datetime
import emoji

def replace_emojis(text, replace_with='[EMOJI]'): 
    return emoji.replace_emoji(text, replace=replace_with)

"""
    If it is an ISO 8601 date it returs it in a different format:
        dd/mm/yy
        H:M:s
    If not just returns back the original data...
"""
def format_date(data): 
    date_str = str(data)
    try: 
        
        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ") 
        formatted_date = date_obj.strftime("%d/%m/%Y\n%H:%M:%S") 
        return formatted_date 
    except ValueError: 
        return data

"""
    Truncates a given string to a max length. If wrap flag is available
    it wraps the string to that lenght.
"""
def truncate_string(text, max_length=70, wrap=False):
    if len(text) > max_length:
        if wrap:
            wrapped_text = '\n'.join([text[i:i+max_length] for i in range(0, len(text), max_length)])
            return wrapped_text
        return text[:max_length] + "..."
    return text

"""
    Recursebly formats a list into a string with some nice viewing format
"""
def strListRecursive(list_in, level=0, max_length=70, tab='  '):
    if not isinstance(list_in, list):
        return list_in
    
    str_data = ""
    for index, value in enumerate(list_in):
        if isinstance(value, dict):
            str_value = strDictRecursive(value, level + 1, max_length)
            str_data += f"{tab*level}- [{index}]:\n{str_value}" if str_value != "" else ""
        elif isinstance(value, list):
            str_value = strListRecursive(value, level + 1, max_length)
            str_data += f"{tab*level}- [{index}]:\n{str_value}" if str_value != "" else ""
        elif value is None:
            continue
        else:
            str_data += f"{tab*level}- [{index}]:{truncate_string(str(value),max_length)}\n"
    return str_data

"""
    Recursebly formats a dict into a string with some nice viewing format
"""
def strDictRecursive(dictionary, level=0, max_length=70, tab='  '):
    if not isinstance(dictionary, dict):
        return dictionary
    
    str_data = ""
    for key, value in dictionary.items():
        if isinstance(value, dict):
            str_value = strDictRecursive(value, level + 1, max_length)
            str_data += f"{tab*level}· {key}:\n{str_value}" if str_value != "" else ""
            
        elif isinstance(value, list):
            str_value = strListRecursive(value, level + 1, max_length)
            str_data += f"{tab*level}· {key}:\n{str_value}" if str_value != "" else ""
        elif value is None:
            continue
        else:
            str_data += f"{tab*level}· {key}: {truncate_string(str(value),max_length)}\n"
    return str_data

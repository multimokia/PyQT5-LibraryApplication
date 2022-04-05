from contextlib import contextmanager
import os
import re
import sys
import time
from typing import Callable, Any


@contextmanager
def suppress_stdout():
    """
    Suppresses stdout temporarily.
    """
    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:
            yield
        finally:
            sys.stdout = old_stdout

#HACK: To workaround not being able to send zip files for assignment submissions
#We're going to install the package ourselves
try:
    import packages.keyboard as keyboard

except ImportError:
    from pip._internal import main as pip_main
    with suppress_stdout():
        pip_main(['install', 'keyboard', '-t', './packages'])

    import packages.keyboard as keyboard

#Validator consts
VALIDATE_INT = r'^[0-9]+$'
VALIDATE_FLOAT = r'^[0-9]+(\.[0-9]+)?$'

#Setup constants for the keyboard keys
KEY_UP = "up"
KEY_DOWN = "down"
KEY_ENTER = "enter"
KEY_SPACE = "space"

#Color consts
TEXT_COLOR_RESET = "\033[0m"
TEXT_COLOR_CYAN = "\033[36m"
TEXT_COLOR_BLACK = "\033[30m"
TEXT_COLOR_GRAY = "\033[90m"

#Text modifiers
TEXT_MOD_RESET = "\033[0m"
TEXT_MOD_BOLD = "\033[1m"
TEXT_MOD_ITALS = "\033[3m"
TEXT_MOD_UNDERLINE = "\033[4m"

TEXT_MOD_INVISIBLE = "\033[8m"
TEXT_MOD_VISIBLE = "\033[28m"

#Custom exception to handle the user backing out of a menu
#NOTE: We consider this a KeyboardInterrupt derivative due to the fact that the user types "NO" to cancel
class UserCancelledException(KeyboardInterrupt):
    pass

class MenuOption:
    """
    Class representing a menu option.
    """
    def __init__(self, prompt:str, result:Any, use_chevron:bool=True):
        self.prompt = prompt
        self.result = result
        self._pointer = '❯' if use_chevron else ' '
        #Hovered state
        self._is_hovered = False

    def __str__(self):
        leading_chars = f'{self._pointer}  ' if self._is_hovered else '   '

        rv = f"{leading_chars}{self.prompt}"
        if self._is_hovered:
            rv = cyan(rv)

        return rv


def menu(prompt:str, *menu_items:MenuOption) -> Any:
    """
    Creates a visual menu in the console which can be navigated with the arrow keys.

    IN:
        prompt: The prompt to display at the top of the menu.
        menu_items: A list of MenuOptions, or individually passed in MenuOption objects.

    OUT:
        The result of the selected MenuOption.
    """
    #Time sleep so we don't pick up the enter keystroke from a previous operation
    time.sleep(0.1)
    current_item = 0
    pressed_key = ""

    while pressed_key not in (KEY_ENTER, KEY_SPACE):
        clearScreen()

        print(cyan("? "), bold(prompt), gray("› Hint - Use the arrow keys to move and hit enter to submit."))

        for index, item in enumerate(menu_items):
            item._is_hovered = index == current_item
            print(item)

        pressed_key = keyboard.read_key()
        time.sleep(0.1)

        if pressed_key == KEY_DOWN:
            current_item += 1

            #Check if we should loop back around
            if current_item > len(menu_items) - 1:
                current_item = 0

        elif pressed_key == KEY_UP:
            current_item -= 1

            #Check if we should loop back around
            if current_item < 0:
                current_item = len(menu_items) - 1

    #Dump the stdin buffer
    #NOTE: sys.stdin.buffer.read/readline both print to stdout for some reason
    #So we redirect stdout to a stringio buffer temporarily to capture the output
    sys.stdin.buffer.raw.readline()
    clearScreen()

    return menu_items[current_item].result

def tableMenu(prompt:str, table_rows:list[str], items:list[Any]) -> Any:
    """
    Table variant of the menu function
    """
    #Time sleep so we don't pick up the enter keystroke from a previous operation
    time.sleep(0.1)
    current_item = 1
    pressed_key = ""

    #Generate Menuitems
    menu_items = list[MenuOption]()

    for index, row in enumerate(table_rows):
        #First 2 rows are the header (we don't include the border because that should highlight on hover)
        if index < 2:
            continue

        #Next up, we need to prepare menuoptions for the rows and separators.
        #NOTE: Starting here, the first item is a separator, and the second is the a selectable item
        #Which means, all even rows are separators, and all odd rows are selectable items
        if index % 2 > 0:
            menu_items.append(MenuOption(row, items[int(index/2) - 1], False))

        #Separators are menuoptions too as they include their own highlighting
        else:
            menu_items.append(MenuOption(row, None, False))

    while pressed_key not in (KEY_ENTER, KEY_SPACE):
        clearScreen()

        print(cyan("? "), bold(prompt), gray("› Hint - Use the arrow keys to move and hit enter to submit."))

        #Print the header bars
        for ind in range(2):
            print(f"   {table_rows[ind]}")

        #Now the actual menu items
        for index, item in enumerate(menu_items):
            item._is_hovered = current_item in (index - 1, index, index + 1)
            print(item)

        pressed_key = keyboard.read_key()
        time.sleep(0.1)

        if pressed_key == KEY_DOWN:
            current_item += 2

            #Check if we should loop back around
            if current_item > len(menu_items) - 1:
                current_item = 1

        elif pressed_key == KEY_UP:
            current_item -= 2

            #Check if we should loop back around
            if current_item < 0:
                current_item = len(menu_items) - 2

    #Dump the stdin buffer
    #NOTE: sys.stdin.buffer.read/readline both print to stdout for some reason
    #So we redirect stdout to a stringio buffer temporarily to capture the output
    sys.stdin.buffer.raw.readline()
    clearScreen()

    return menu_items[current_item].result

##Color Modifiers
def cyan(text):
    """
    Returns the text in cyan.
    """
    return f"{TEXT_COLOR_CYAN}{text}{TEXT_COLOR_RESET}"

def black(text):
    """
    Returns the text in black.
    """
    return f"{TEXT_COLOR_BLACK}{text}{TEXT_COLOR_RESET}"

def gray(text):
    """
    Returns the text in gray.
    """
    return f"{TEXT_COLOR_GRAY}{text}{TEXT_COLOR_RESET}"

##Text Decoration
def bold(text):
    """
    Returns the text in bold.
    """
    return f"{TEXT_MOD_BOLD}{text}{TEXT_MOD_RESET}"

def underline(text):
    """
    Returns the text in underline.
    """
    return f"{TEXT_MOD_UNDERLINE}{text}{TEXT_MOD_RESET}"

def italics(text):
    """
    Returns the text in italics.
    """
    return f"{TEXT_MOD_ITALS}{text}{TEXT_MOD_RESET}"

def clearScreen() -> None:
    """
    Clears the screen.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

def validatedInput(prompt:str, regex:str) -> str:
    """
    Prompts the user for input and allows for arbitrary validation through regex

    IN:
        prompt: prompt to display to the user
        regex: regex to validate the input

    OUT:
        the input that the user entered
    """
    while True:
        clearScreen()
        user_input = input(prompt).strip()

        if re.match(regex, user_input):
            return user_input

        #We raise a user cancelled exception which is expected to be caught by the top level caller
        elif user_input == "NO":
            raise UserCancelledException()

def validatedIntInput(prompt:str) -> int:
    """
    Prompts the user for an integer.

    IN:
        prompt: prompt to display to the user

    OUT:
        the integer that the user entered
    """
    return int(validatedInput(prompt, VALIDATE_INT))

def validatedFloatInput(prompt:str) -> float:
    """
    Prompts the user for a float.

    IN:
        prompt: prompt to display to the user

    OUT:
        the float that the user entered
    """
    return float(validatedInput(prompt, VALIDATE_FLOAT))

def conditionalIntInput(prompt:str, predicate: Callable[[int], bool]) -> int:
    """
    Prompts the user for an integer.

    IN:
        prompt: prompt to display to the user
        predicate: function to validate the input

    OUT:
        the integer that the user entered
    """
    result = False
    rv: int
    while not result:
        rv = validatedIntInput(prompt)
        result = predicate(rv)

    return rv

def enterToContinue(wait_time:float=0.1) -> None:
    """
    Waits for the user to press enter to continue.

    IN:
        wait_time: the time to wait before allowing a keystroke to be entered.
    """
    time.sleep(wait_time)
    input(italics(gray("(Press enter to continue.)")))

def waitKey() -> None:
    """
    Waits for a key to be pressed
    """
    if os.name == 'nt':
        print(gray(italics("Press any key to continue...")))
        os.system("pause")

    else:
        os.system(f'read -s -n 1 -p "{gray(italics("Press any key to continue..."))}"')
        print()

def printTable(header:list, rows:list, amt_padding:int=5) -> None:
    """
    Prints a table to the console. See buildTable for args
    """
    printLines(*buildTable(header, rows, amt_padding))

def buildTable(header:list, rows:list, amt_padding:int=5) -> list[str]:
    """
    Prints a table to the console.

    ASSUMES:
        rows is a list of objects implementing toTuple()

    IN:
        header: the header row of the table
        rows: a list of objects implementing toTuple() to be used as row data
        amt_padding: the amount of spaces used to pad each column

    OUT:
    """
    padding_added = amt_padding * 2
    table_content = [header]

    for row in rows:
        table_content.append(row.toTuple())

    #Get the max length of each column
    max_lengths = []
    for index in range(len(header)):
        largest_length = 0
        for row_index in range(len(table_content)):
            cell_length = len(str(table_content[row_index][index]))
            if cell_length > largest_length:
                largest_length = cell_length

        max_lengths.append(largest_length + padding_added)

    return buildTableWithCellLengths(header, rows, max_lengths)

def buildTableWithCellLengths(header:list, rows:list, cell_lengths:list) -> list[str]:
    """
    Prints a table to the console.

    ASSUMES:
        rows is a list of objects implementing toTuple()

    IN:
        header: the header row of the table
        rows: a list of objects implementing toTuple() to be used as row data
        cell_lengths: a list of cell lengths, one for each column
    """
    rv = list[str]()

    def _formatFloat(infloat:float):
        #NOTE: Because in this application, floats are always related to money, we'll prefix the float with $
        return f"${infloat:.2f}"

    def _formatRow(row:list):
        rv = "|"

        for column_num, item in enumerate(row):
            curr_item_str = ""
            if isinstance(item, float):
                curr_item_str = _formatFloat(item)
            else:
                curr_item_str += str(item)

            rv += curr_item_str.center(cell_lengths[column_num]) + "|"

        return rv

    TABLE_TOP_BOTTOM_BORDER = "+"
    TABLE_ROW_SPLIT = "|"

    #Generate the row splitters of the table as this depends on the cell lengths
    for cell_index, cell_length in enumerate(cell_lengths):
        TABLE_TOP_BOTTOM_BORDER += ("-" * cell_length) + "+"
        TABLE_ROW_SPLIT += ("-" * cell_length)

        if (cell_index != len(cell_lengths) - 1):
            TABLE_ROW_SPLIT += "+"

    TABLE_ROW_SPLIT += "|"

    #Print table top
    rv.append(TABLE_TOP_BOTTOM_BORDER)
    #Then the headerbar
    rv.append(_formatRow(header))
    #Then the row split
    rv.append(TABLE_ROW_SPLIT)

    #Now print the rows
    for row_num, row in enumerate(rows):
        rv.append(_formatRow(row.toTuple()))
        rv.append(TABLE_ROW_SPLIT if row_num != len(rows) - 1 else TABLE_TOP_BOTTOM_BORDER)

    return rv

def printLines(*lines):
    for line in lines:
        print(line)

# STUDENT version for Project 1.
# TPRG2131 Fall 2024
# Chamath Kulathilaka (100889193)
# Updated Phil J (Fall 2024)
# 
# Louis Bertrand
# Oct 4, 2021 - initial version
# Nov 17, 2022 - Updated for Fall 2022.
# 

# PySimpleGUI recipes used:
#
# Persistent GUI example
# https://pysimplegui.readthedocs.io/en/latest/cookbook/#recipe-pattern-2a-persistent-window-multiple-reads-using-an-event-loop
#
# Asynchronous Window With Periodic Update
# https://pysimplegui.readthedocs.io/en/latest/cookbook/#asynchronous-window-with-periodic-update

# This program is strictly my own work. Any material
# beyong course learning materials that is taken from
# the Web or other sources is properly cited, giving
# credit to original author (s).

import PySimpleGUI as sg
from time import sleep

#Where am I?
hardware_present = False
try:
    import gpiozero
    from gpiozero import Servo, Button
    #servo = Servo(17)
    key1 = Button(5)
    hardware_present = True
except ModuleNotFoundError:
    print("Not on a Raspberry Pi or gpiozero not installed.")
# Setting this constant to True enables the logging function
# Set it to False for normal operation
TESTING = True
# Print a debug log string if TESTING is True, ensure use of Docstring, in definition
def log(s):
    """Log debugging information if TESTING is True."""
    if TESTING:
        print(s)

# The vending state machine class holds the states and any information
# that "belongs to" the state machine. In this case, the information
# is the products and prices, and the coins inserted and change due.
# For testing purposes, output is to stdout, also ensure use of Docstring, in class

class VendingMachine:
    """The vending machine state machine."""
    PRODUCTS = {
        "chips": ("CHIPS", 150, 10),   # $1.50, 10 items in stock
        "soda": ("SODA", 125, 8),      # $1.25, 8 items in stock
        "candy": ("CANDY", 100, 5),    # $1.00, 5 items in stock
        "gum": ("GUM", 50, 20),        # $0.50, 20 items in stock
        "cookie": ("COOKIE", 175, 3),  # $1.75, 3 items in stock
    }

    COINS = {
        "nickel": ("5¢", 5),
        "dime": ("10¢", 10),
        "quarter": ("25¢", 25),
        "loonie": ("$1", 100),
        "toonie": ("$2", 200),
    }

    def __init__(self):
        self.state = None  # current state
        self.states = {}  # dictionary of states
        self.event = ""  # no event detected
        self.amount = 0  # amount from coins inserted so far
        self.change_due = 0  # change due after vending
        self.servo = Servo(17) if hardware_present else None
        # Build a list of coins in descending order of value

    def add_state(self, state):
        self.states[state.name] = state

    def go_to_state(self, state_name):
        if self.state:
            log(f"Exiting {self.state.name}")
            self.state.on_exit(self)
        self.state = self.states[state_name]
        log(f"Entering {self.state.name}")
        self.state.on_entry(self)

    def update(self):
        if self.state:
            self.state.update(self)

    def add_coin(self, coin):
        self.amount += self.COINS[coin][1]
        print(f"Coin inserted: {coin}, Total: ${self.amount / 100:.2f}")
        return self.amount

    def button_action(self):
        self.event = 'RETURN'
        self.update()


    def dispense_product(self, product):
        if hardware_present and self.servo:
            log(f"Dispensing {self.PRODUCTS[product][0]} via servo")
            self.servo.min()
            sleep(0.5)# Simulate servo motion
            self.servo.mid()
            sleep(0.5)


# Parent class for the derived state classes
# It does nothing. The derived classes are where the work is done.
# However this is needed. In formal terms, this is an "abstract" class.

class State:
    """Abstract superclass for states."""
    _NAME = ""

    def __init__(self):
        pass

    @property
    def name(self):
        return self._NAME

    def on_entry(self, machine):
        pass

    def on_exit(self, machine):
        pass

    def update(self, machine):
        pass
# In the waiting state, the machine waits for the first coin
class WaitingState(State):
    _NAME = "waiting"
    def update(self, machine):
        if machine.event in machine.COINS:
            machine.add_coin(machine.event)
            machine.go_to_state("add_coins")
# Additional coins, until a product button is pressed
class AddCoinsState(State):
    _NAME = "add_coins"
    def update(self, machine):
        if machine.event == "RETURN":
            machine.change_due = machine.amount # return entire amount
            machine.amount = 0
            machine.go_to_state("count_change")
        elif machine.event in machine.COINS:
            machine.add_coin(machine.event)
        elif machine.event in machine.PRODUCTS:
            product = machine.event
            label, price, stock = machine.PRODUCTS[product]
            if stock <= 0:
                print(f"{machine.PRODUCTS[product][0]} is SOLD OUT")
            elif machine.amount >= price:
                machine.PRODUCTS[product] = (machine.PRODUCTS[product][0], price, stock - 1)
                machine.change_due = machine.amount - price
                machine.amount = 0
                machine.go_to_state("deliver_product")
            elif machine.amount < price:
                print(f"Not enough money. Price: ${price / 100:.2f}") # Not enough money for the product
# Print the product being delivered
class DeliverProductState(State):
    _NAME = "deliver_product"
    def on_entry(self, machine):
        # Deliver the product and change state
        product = machine.event
        machine.dispense_product(product)
        if machine.change_due > 0:
            machine.go_to_state("count_change")
        else:
            machine.go_to_state("waiting")
# Count out the change in coins 
class CountChangeState(State):
    _NAME = "count_change"
    def on_entry(self, machine):
        # Return the change due and change state
        print(f"Change due: ${machine.change_due / 100:.2f}")
        log(f"Returning change: {machine.change_due}")

    def update(self, machine):
        coin_values = sorted([value[1] for value in machine.COINS.values()], reverse=True)
        for coin in coin_values:
            while machine.change_due >= coin:
                print(f"Returning {coin}¢")
                machine.change_due -= coin
        if machine.change_due == 0:
            machine.go_to_state("waiting") # No more change due, done
# Main Program
if __name__ == "__main__":
    # GUI Setup
    sg.theme("BluePurple")
 
    coin_col = [[sg.Text("INSERT COINS", font=("Helvetica", 20))]]
    for coin in VendingMachine.COINS:
        coin_col.append([sg.Button(coin, font=("Helvetica", 16))])

    select_col = [[sg.Text("SELECT ITEM", font=("Helvetica", 20))]]
    for product, (label, price, stock) in VendingMachine.PRODUCTS.items():
        status = f"{label} - ${price / 100:.2f} ({stock} left)" if stock > 0 else f"{label} - SOLD OUT"
        select_col.append([sg.Button(status, font=("Helvetica", 14), key=product, disabled=stock <= 0)])

    layout = [
        [sg.Column(coin_col, vertical_alignment="TOP"), sg.VSeparator(), sg.Column(select_col, vertical_alignment="TOP")],
        [sg.Button("RETURN", font=("Helvetica", 14))]
    ]

    window = sg.Window("Vending Machine", layout)

    # Initialize State Machine
    vending = VendingMachine()
    vending.add_state(WaitingState())
    vending.add_state(AddCoinsState())
    vending.add_state(DeliverProductState())
    vending.add_state(CountChangeState())
    
    vending.go_to_state('waiting')
     


    
     # Checks if being used on Pi
    if hardware_present:
        # Set up the hardware button callback (do not use () after function!)
        key1.when_pressed = vending.button_action
            
    # The Event Loop: begin continuous processing of events
    # The window.read() function reads events and values from the GUI.
    # The machine.event variable stores the event so that the
    # update function can process it.
    # Now that all the states have been defined this is the
    # main portion of the main program.

# Event Loop
    while True:
        event, values = window.read(timeout=10)
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        if event != "__TIMEOUT__":
            #log(f"Event: {event}")
            vending.event = event
            vending.update()
            if event in vending.PRODUCTS:  # Check if the event is a product
                label, price, stock = vending.PRODUCTS[event]
                # Update button text to reflect new stock
                stock_text = f"{label} - ${price / 100:.2f} ({stock} left)" if stock > 0 else f"{label} - SOLD OUT"
                window[event].update(text=stock_text, disabled=(stock <= 0))

    window.close()
    print("Normal exit")

from Project_final_CNK import VendingMachine, WaitingState, AddCoinsState, DeliverProductState, CountChangeState

def test_VendingMachine():
    vending = VendingMachine()
    vending.add_state(WaitingState())
    vending.add_state(AddCoinsState())
    vending.add_state(DeliverProductState())
    vending.add_state(CountChangeState())
    
    vending.go_to_state("waiting")
    assert vending.state.name == "waiting"
    
    vending.event = 'toonie'
    vending.update()
    assert vending.state.name == "add_coins"
    assert vending.amount == 200
    
    
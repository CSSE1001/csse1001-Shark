#!/usr/bin/env python3
###################################################################
#
#   CSSE1001/7030 - Assignment 1 solution
#
###################################################################


# 2.2.1
def make_initial_state(supporters):
    """
    Takes the number of supporters for each team and gives back the initial
    state.

    make_initial_state(int) -> str
    """
    
    return "TA" * supporters + "__"

# 2.2.2
def make_position_string(length):
    """
    Takes the length of the state and returns a string of the same length
    containing digits from 0 to 9, in order and repeated as many times as
    needed.

    make_position_string(int) -> str
    """

    output = ""

    for i in range(length):
        output += str(i % 10)

    return output

# 2.2.3
def num_diffs(state):
    """
    Takes a state and returns the number of differences between adjacent
    entries.

    num_diffs(str) -> int
    """

    count = 0

    for i in range(len(state) - 1):
        if state[i] != state[i + 1]:
            count += 1

    return count


# 2.2.4
def position_of_blanks(state):
    """
    Takes a state and returns the position of the first blank entry.

    position_of_blanks(str) -> int
    """

    return state.find('_')


# 2.2.5
def make_move(state, position):
    """
    Takes a state and a position and returns a new state where the pair at the
    given position have been swapped with the blank entries.

    Precondition: |position - position_of_blanks| >= 2

    make_move(str, int) -> str
    """

    blank_position = position_of_blanks(state)

    substring_at_position = state[position:position+2]
    state1 = state.replace('__', substring_at_position)
    part1 = state1[:position]
    part2 = state1[position+2:]

    return part1 + '__' + part2


# 2.2.6
def show_current_state(states):
    """
    Prints the state information for the current state as required for the
    user interaction, where states is the list of states representing the
    history of moves, and the current state is the last state in states.

    show_current_state([str]) -> None
    """

    state = states[-1]
    position_string = make_position_string(len(state))
    moves = len(states) - 1
    diffs = num_diffs(state)

    print(position_string)
    print(state, diffs, moves)


# 2.2.7
def interact():
    """
    Handles top-level interaction with user.

    interact() -> None
    """

    supporters = int(input("How many supporters from each team? "))
    
    states = []
    states.append(make_initial_state(supporters))

    while True:
        show_current_state(states)

        cmd = input("? ").strip()

        if cmd == "b":
            # Don't go back if we're at the start already!
            if len(states) > 1:
                states.pop()
        elif cmd == "q":
            break
        else:
            pos = int(cmd)
            states.append(make_move(states[-1], pos))


##################################################
# !!!!!! Do not change (or add to) the code below !!!!!
# 
# This code will run the interact function if
# you use Run -> Run Module  (F5)
# Because of this we have supplied a "stub" definition
# for interact above so that you won't get an undefined
# error when you are writing and testing your other functions.
# When you are ready please change the definition of interact above.
###################################################

if __name__ == '__main__':
    interact()
